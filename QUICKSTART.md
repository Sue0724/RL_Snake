# Snake-RL 接口速查

给需要调用环境或 Agent 的成员。**权威定义在 [`docs/INTERFACE.md`](docs/INTERFACE.md)**，本页只是速查，冲突时以该文件为准。

> 截至 10-10，环境、Q 网络、Replay Buffer 和 DQNAgent 已实现；train.py 的训练循环与基础日志代码已补齐，尚未运行验证。evaluate.py 尚待实现，DQN 基线的学习效果仍待验收。

---

## 一、装环境

```bash
conda create -n snake-rl python=3.10 -y
conda activate snake-rl
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

---

## 二、环境

```python
from common.config import Config
from env.snake_env import SnakeEnv

cfg = Config()
env = SnakeEnv(cfg)

state, info = env.reset(seed=cfg.seed)
next_state, reward, terminated, truncated, info = env.step(action)
env.render()
```

| 项 | 值 |
|---|---|
| `state` | `np.ndarray`，shape `(state_dim,)`，`float32`；默认 `"v1"` 时为 `(11,)` |
| `action` | `int`：`0` 直行 / `1` 左转 / `2` 右转（相对动作，无 180° 反向） |
| `terminated` | 撞墙或撞自身 |
| `truncated` | 达到 `max_steps_per_episode`（默认 500） |
| `env.state_dim` | 随 `state_mode` 变化；默认 `"v1"` 时为 `11` |
| `env.n_actions` | `3` |

### State V1（11 维，默认）

| 索引 | 含义 |
|---|---|
| 0 / 1 / 2 | `danger_straight` / `danger_left` / `danger_right` |
| 3 / 4 / 5 / 6 | `moving_up` / `moving_down` / `moving_left` / `moving_right`（one-hot） |
| 7 / 8 / 9 / 10 | `food_up` / `food_down` / `food_left` / `food_right`（**不互斥**，左上同时为 1） |

**State V2（20 维，预定方案，未冻结）**：V1 的 11 维 + `food_distance` + 蛇头周围 8 格 `local_ring`，
`state_mode="v2"` 启用。完整规格见 `docs/INTERFACE.md` §4。

⚠️ **建网络一律写 `DQNAgent(env.state_dim, env.n_actions, config)`，不要写死 `11` 和 `3`。**
V2 维度不同，写死的代码在切换 `state_mode` 后会直接抛形状错误，且报错位置离原因很远。

### `info` 字段

```text
score  steps  snake_length
food_reward  death_penalty  distance_reward  step_reward
```

四个分项之和等于 `reward`。

### ⚠️ Bellman target 必须区分 terminated 与 truncated

```python
target = reward + (1 - terminated) * gamma * max_a Q_target(next_state, a)
```

`truncated` **不参与**该式 —— 截断时蛇仍然活着，仍应 bootstrap。把截断当作真终止会让 Q 值被系统性低估。

---

## 三、配置

```python
from common.config import Config, parse_args

cfg = parse_args()        # 命令行覆盖，未传入的字段用默认值
```

```bash
python train.py --algorithm dqn --seed 42
```

21 个字段见 `common/config.py`。每个 run 存档：

```python
import dataclasses, json

with open(run_dir / "config.json", "w", encoding="utf-8") as f:
    json.dump(dataclasses.asdict(cfg), f, indent=2, ensure_ascii=False)
```

---

## 四、Agent

### 已实现的基础组件（第四步与第五步）

```python
import torch
from algorithms.networks import QNetwork
from common.replay_buffer import ReplayBuffer

net = QNetwork(env.state_dim, env.n_actions, cfg.hidden_dim)
buffer = ReplayBuffer(cfg.buffer_size, seed=cfg.seed)

state, _ = env.reset(seed=cfg.seed)
next_state, reward, terminated, truncated, _ = env.step(0)
buffer.add(state, 0, reward, next_state, terminated, truncated)

# 这里采样 1 条，仅演示数据流；正式训练须等待回放池预热。
batch = buffer.sample(1)
q_values = net(torch.from_numpy(batch["states"]))
print(q_values.shape)  # (1, env.n_actions)
env.close()
```

Q 网络默认结构为 `state_dim → 128 → 128 → n_actions`，中间使用 ReLU，
输出是动作价值，允许负数，不做概率归一化。刚创建的网络尚未训练。
Replay Buffer 保存六项经历的状态副本，满容量后覆盖最旧记录，随机无放回采样。
正式训练前需要同时满足 `len(buffer) >= cfg.min_buffer_size` 和
`len(buffer) >= cfg.batch_size`；完整 batch 的 shape/dtype 见 `INTERFACE.md` §12。

### DQNAgent（第六步与第七步已实现）

```python
from algorithms.dqn import DQNAgent

env = SnakeEnv(cfg)
agent = DQNAgent(state_dim=env.state_dim, n_actions=env.n_actions, config=cfg)
buffer = ReplayBuffer(cfg.buffer_size, seed=cfg.seed)
state, _ = env.reset(seed=cfg.seed)

action = agent.select_action(state, training=True)
next_state, reward, terminated, truncated, _ = env.step(action)
buffer.add(state, action, reward, next_state, terminated, truncated)
agent.on_env_step()  # 走完一步后计步并衰减，包含终止/截断的最后一步

ready = len(buffer) >= max(cfg.min_buffer_size, cfg.batch_size)
batch = buffer.sample(cfg.batch_size) if ready else None
loss = agent.update(batch)  # 默认配置下此时尚在预热期，返回 None
env.close()
```

模型存取使用实际文件路径：

```python
agent.save(path)
agent.load(path)
```

`training=False` 时纯贪心 —— **评估阶段必须用 `False`**。
选择动作不改变 epsilon；评估不调用训练更新，也不计入训练步数。
训练循环须在局结束后重新 `env.reset()`，epsilon 跨局延续。

Online Network 根据记录的动作提取 Q 值；Target Network 在无梯度模式下计算
下一状态的最大 Q 值，仅 `terminated` 屏蔽未来价值。使用 Smooth L1 loss 和 Adam
更新 Online；每 `cfg.target_update_interval` 次成功更新后同步 Target。
checkpoint 恢复智能体状态，回放池与环境状态需由训练框架另行管理。

batch 中每条转移必须保留两个独立标记：

```python
(state, action, reward, next_state, terminated, truncated)
```

---

## 五、实验输出

```text
results/logs/{experiment}_{algorithm}_{state}_{reward}_seed{seed}_{timestamp}/
├── config.json
├── metrics.csv
├── summary.json
└── checkpoint.pt
```

`metrics.csv` 列：

```text
episode  episode_return  score  episode_length  epsilon  loss  global_step
```

每次 run 写入**新建**目录，不复用已存在的 run 目录。

---

## 六、运行 DQN 训练（第八步的训练与日志部分）

在项目根目录打开终端。本机之前安装依赖使用的是 `python3`。

先运行 100 局短程调试，不修改算法默认参数：

```bash
python3 train.py --num_episodes 100 --seed 42 --experiment debug_baseline --log_every 10
```

默认回放池需积累 1,000 条经历才开始更新。如果短程运行的总步数不足 1,000，
`updates=0` 和 `loss=预热` 是正常现象。需要专门检查更新链路时，用如下调试命令：

```bash
python3 train.py --num_episodes 100 --seed 42 --min_buffer_size 64 --experiment debug_update --log_every 10
```

此命令仅缩短预热；调试结果不用于正式性能结论。调试结束后恢复默认预热，
按相同环境步数分别训练三个种子：

```bash
python3 train.py --total_steps 50000 --seed 42 --experiment baseline
python3 train.py --total_steps 50000 --seed 43 --experiment baseline
python3 train.py --total_steps 50000 --seed 44 --experiment baseline
```

50,000 步是首轮训练预算建议，不保证已经收敛。传入 `--total_steps` 后，
它覆盖 `--num_episodes`，严格达到该环境步数才停止；未传入时按完整局数停止。
预算在局中用完时，该局仍写入 CSV，但 `episode_complete=False`，不纳入完整局汇总；
这不改变环境的 `terminated/truncated` 标记。

每局的循环顺序：选动作 → `env.step` → 回放池保存 → `on_env_step` 计步和衰减
→ 预热足够时采样并更新 → 结束后记录日志并 `reset()`。只有第一局显式传 seed，
后续沿用环境 RNG，避免每局重复相同初始局面。

终端打印的含义：

| 字段 | 含义 |
|---|---|
| `episode` | 当前局编号，从 1 开始 |
| `step` | 累计训练环境步数 |
| `score` | 这一局吃到的食物数 |
| `return` | 这一局所有 reward 之和 |
| `epsilon` | 本局结束后的探索率，下一步使用它 |
| `loss` | 本局实际网络更新的平均 loss；未更新时显示“预热” |
| `updates` | 累计成功的梯度更新次数 |

终端首行打印本次输出目录。打开该目录查看：

- `config.json`：完整 Config，记录真实使用的超参数。
- `metrics.csv`：每局一行，包含既有七项指标及 run 标识、两个结束标记、是否完整局等。
  无更新时 `loss` 单元格为空，不能把它当作零误差。
- `summary.json`：完整训练局的均值/标准差/最高分及运行状态；
  `metrics_scope=training`，不是独立评估结果。CLI 自有运行选项存入 `run_settings`。
- `checkpoint.pt`：该 run 最新模型；开始时、每 100 个完整局及正常结束时保存。
  `--checkpoint_every` 可调整间隔。

CSV 每局写入后立即 flush；每次运行新建目录，即使相同 seed 也不覆盖历史 run。
按 `Ctrl+C` 会尝试保存当前模型和中断摘要；强制杀进程或关机不能保证触发保存。
checkpoint 不包含 Replay Buffer 和环境状态，本入口尚不支持完整续训。
训练默认无窗口，Torch CPU 计算线程默认 1，可用 `--torch_threads` 调整并记录。

下一步依次检查：日志/模型是否生成 → 是否进入网络更新 → 更长预算下有无 NaN/Inf
→ 实现独立 evaluate，关闭探索和更新，以相同评估种子与 Random 比较。
训练 score 上升或 loss 下降都不能单独代替最后的独立评估。

**验证状态：此次新增训练与日志代码尚未运行验证（Not Tested）。**

---

## 七、权威文档

| 主题 | 文档 |
|---|---|
| 接口定义 | `docs/INTERFACE.md` |
| AI 开发规范 | `docs/AI_DEVELOPMENT_RULES.md` |
| 实验协议 | `docs/EXPERIMENT_PROTOCOL.md` |
| 分工与协作 | `docs/COLLABORATION_RULES.md` |
| 当前进度 | `docs/PROJECT_STATUS.md` |
| 阶段验收 | `docs/STAGE_CHECKLIST.md` |
| 操作日志 | `memory.md` |
