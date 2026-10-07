# Snake-RL 接口速查

给需要调用环境或 Agent 的成员。**权威定义在 [`docs/INTERFACE.md`](docs/INTERFACE.md)**，本页只是速查，冲突时以该文件为准。

> `env/snake_env.py` 与 `algorithms/*.py` 尚未实现。本页定义的是它们实现后必须遵守的接口。

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

20 个字段见 `common/config.py`。每个 run 存档：

```python
import dataclasses, json

with open(run_dir / "config.json", "w", encoding="utf-8") as f:
    json.dump(dataclasses.asdict(cfg), f, indent=2, ensure_ascii=False)
```

---

## 四、Agent

```python
agent = DQNAgent(state_dim=env.state_dim, n_actions=env.n_actions, config=cfg)

action = agent.select_action(state, training=True)
loss   = agent.update(batch)
agent.save(path)
agent.load(path)
```

`training=False` 时纯贪心 —— **评估阶段必须用 `False`**。

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

## 六、权威文档

| 主题 | 文档 |
|---|---|
| 接口定义 | `docs/INTERFACE.md` |
| AI 开发规范 | `docs/AI_DEVELOPMENT_RULES.md` |
| 实验协议 | `docs/EXPERIMENT_PROTOCOL.md` |
| 分工与协作 | `docs/COLLABORATION_RULES.md` |
| 当前进度 | `docs/PROJECT_STATUS.md` |
| 阶段验收 | `docs/STAGE_CHECKLIST.md` |
| 操作日志 | `memory.md` |
