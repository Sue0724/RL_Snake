# 接口定义

Stage 0 冻结。本文件定义 Snake-RL 的 Environment API、动作空间、状态表示、`info` 字段、随机种子控制、默认参数、实验输出约定与 Agent API。速查版见根目录 `QUICKSTART.md`。

冻结后调用方不得单方面修改。如需变更，按 `AI_DEVELOPMENT_RULES.md` §20 执行：说明原因、列出影响文件、给出方案、等待确认，然后更新全部调用方与文档、完成集成测试，并在 `PROJECT_STATUS.md` 记录。

---

## 1. Environment API

采用 Gymnasium 风格返回值。

```python
env = SnakeEnv(config)

state, info = env.reset(seed=None)
next_state, reward, terminated, truncated, info = env.step(action)
env.render()
```

| 项 | 类型 | 说明 |
|---|---|---|
| `state` | `np.ndarray`，shape `(11,)`，dtype `float32` | 见第 4 节 |
| `reward` | `float` | 标量即时奖励 |
| `terminated` | `bool` | 撞墙或撞自身 |
| `truncated` | `bool` | 步数达 `max_steps_per_episode` 且未终止 |
| `info` | `dict` | 见第 5 节 |

环境提供的只读属性与方法：

```python
env.state_dim   # 11
env.n_actions   # 3
env.close()     # 释放渲染资源；未使用渲染时为空操作
```

**为什么区分 `terminated` 与 `truncated`**：截断（超时）时蛇仍然活着，bootstrap 仍应进行：

```python
target = reward + (1 - terminated) * gamma * max_a Q_target(next_state, a)
```

若把截断视为真终止，`target = reward`，Q 值被系统性低估。

**生命周期**：`reset()` 之前、以及 `terminated or truncated` 为 True 之后，都不得调用 `step()`，调用方应先 `reset()`。违反时抛 `RuntimeError`。

选择硬失败而不是静默忽略：训练循环漏写 `reset()` 是确定性 bug，第一局就会暴露；静默忽略会让后续所有 transition 都变成假的终止样本，污染 Replay Buffer 且不易察觉。

---

## 2. 动作空间

相对动作，共 3 个：

```text
0 = 直行（保持当前朝向）
1 = 左转（逆时针 90°）
2 = 右转（顺时针 90°）
```

相对动作不会产生 180° 反向，无需额外禁手。

---

## 3. 坐标与方向

棋盘为 `board[row][col]`，`row` 向下增大，`col` 向右增大。

| 朝向 | 移动 |
|---|---|
| `up` | `row - 1` |
| `down` | `row + 1` |
| `left` | `col - 1` |
| `right` | `col + 1` |

初始朝向固定为 `right`。

---

## 4. 状态表示

### State V1（冻结，11 维 `float32`）

以蛇头朝向为"前方"，危险与食物均相对蛇头感知。

| 索引 | 名称 | 含义 | 取值 |
|---|---|---|---|
| 0 | `danger_straight` | 直行后的落点是否撞墙或撞蛇身 | 0 / 1 |
| 1 | `danger_left` | 左转后的落点是否撞墙或撞蛇身 | 0 / 1 |
| 2 | `danger_right` | 右转后的落点是否撞墙或撞蛇身 | 0 / 1 |
| 3 | `moving_up` | 蛇头朝向 | 0 / 1 |
| 4 | `moving_down` | 蛇头朝向 | 0 / 1 |
| 5 | `moving_left` | 蛇头朝向 | 0 / 1 |
| 6 | `moving_right` | 蛇头朝向 | 0 / 1 |
| 7 | `food_up` | 食物行号 < 蛇头行号 | 0 / 1 |
| 8 | `food_down` | 食物行号 > 蛇头行号 | 0 / 1 |
| 9 | `food_left` | 食物列号 < 蛇头列号 | 0 / 1 |
| 10 | `food_right` | 食物列号 > 蛇头列号 | 0 / 1 |

说明：

- `[3:7]` 是 one-hot。
- `[7:11]` **不互斥**：食物在左上时 `food_up` 与 `food_left` 同时为 1。
- `danger_*` 按"执行该动作后蛇头的新位置"判断。

### 碰撞判定（`danger_*` 与 `step()` 共用同一条规则）

```text
落点出界                    -> 碰撞
落点在蛇身（不含蛇尾）       -> 碰撞
落点 == 蛇尾                -> 不碰撞
```

蛇尾是唯一例外：它在同一步会腾出格子，所以落进蛇尾合法。蛇身中段不动，落进去就是死。

"吃到食物时尾巴不动"不需要单独分支：吃到食物意味着落点 == 食物，而食物永远生成在空格子，所以此时落点 != 蛇尾 自动成立，两种情形不会同时出现。

`danger_*` 必须与 `step()` 共用同一个判定函数。若 `danger_*` 用"含蛇尾"的保守版本，状态就会把"其实能走"的方向标成危险，等于给网络喂错标签。

### State V2

Stage 4 定义，在 V1 基础上**追加维度**，不修改 V1 已冻结的 11 维语义。

`state_mode` 取值：`"v1"`（默认）。其他取值抛 `NotImplementedError`。

---

## 5. `info` 字段

`reset()` 与每次 `step()` 返回同一组 key。`reset()` 时四个分项均为 0。

| key | 类型 | 说明 |
|---|---|---|
| `score` | `int` | 已吃到食物数 |
| `steps` | `int` | 本 episode 已走步数 |
| `snake_length` | `int` | 当前蛇长 |
| `food_reward` | `float` | 本步吃食物奖励，未吃到为 0 |
| `death_penalty` | `float` | 本步死亡惩罚，未死亡为 0 |
| `distance_reward` | `float` | 本步距离 shaping 项，`sparse` 模式恒为 0 |
| `step_reward` | `float` | 本步每步惩罚项，`sparse` 模式恒为 0 |

四个分项之和等于 `reward`：

```text
reward == food_reward + death_penalty + distance_reward + step_reward
```

**为什么要分项**：`EXPERIMENT_PROTOCOL.md` 第七节要求 Reward Shaping 实验必须同时记录 total reward 与 actual score，防止"高 Return 低 Score"的伪改进。分项能直接看出 Return 是被哪一项抬高的。

---

## 6. 奖励

`reward_mode` 由配置切换，环境内部分支计算，**不为每种奖励复制环境**。

### `"sparse"`（基线，冻结）

```text
吃到食物： +10
死亡：     -10
普通移动：   0
```

### shaping 模式

`"distance"` 与 `"distance_step"` 的具体系数在 Stage 5 定义并冻结。Stage 0 只冻结：

- 切换 key 为 `reward_mode`
- 各 shaping 项分别写入 `info` 对应字段
- 每项量级受限，不得压过吃食物奖励（见 `README.md` 风险一）

### 非法取值

未实现的 `reward_mode` 抛 `NotImplementedError`，**不做静默回退到 `sparse`**：回退会让 Stage 5 的 shaping 实验"看起来做了、其实没做"，是最难查的一类错误。校验在 `SnakeEnv.__init__` 中完成，配置写错时立刻暴露，而不是训练若干局之后。

---

## 7. 随机种子

### 环境内部

环境持有自己的随机数生成器：

```python
self.np_random = np.random.default_rng(seed)
```

- `reset(seed=int)` → 用该 seed **重建** `np_random`
- `reset(seed=None)` → 沿用当前 `np_random` 状态，连续 episode 不会重复同一局

初始蛇位置与食物生成**全部**经由 `self.np_random`。禁止使用全局 `np.random` 或 Python `random`，否则相同 seed 无法复现相同轨迹。

### 全局（算法侧）

`common/utils.py` 提供：

```python
set_global_seed(seed: int) -> None
```

统一设置 Python `random`、NumPy、PyTorch（含 CUDA）。训练脚本开头调用一次，并把同一个 seed 传入 `env.reset(seed=seed)`。

见 `EXPERIMENT_PROTOCOL.md` 第三节。

---

## 8. 默认参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `board_size` | `10` | 10×10，共 100 格 |
| `initial_length` | `3` | 初始蛇长 |
| `max_steps_per_episode` | `500` | 超出则 `truncated=True` |
| `initial_head` | `None` | `None` = 随机；传 `(row, col)` 固定初始蛇头 |
| `initial_direction` | `right` | 固定，不是配置 key |
| `render_mode` | `None` | `None` / `"human"` / `"rgb_array"` |

这三个数值在正式实验期间不得更改，否则实验不可比。Stage 2 训练后可依据 `metrics.csv` 中 `episode_length` 的分布与 `truncated` 出现频率复核 `max_steps_per_episode` 是否偏小；复核须在正式实验开始前完成。

### 初始蛇位置

`initial_head is None` 时随机，经 `self.np_random`：

```text
head_row ∈ [0, board_size)
head_col ∈ [initial_length - 1, board_size)
```

蛇身自蛇头向 `initial_direction` 的**反方向**延伸（朝右时蛇身在左侧，即 `col-1`、`col-2`…），所以 `head_col` 的下界是 `initial_length - 1`，保证蛇身不越界、无需拒绝采样。

`initial_head` 非 `None` 时直接使用该坐标，蛇身同样按上述规则延伸；蛇身放不下时抛 `ValueError`。

### 食物生成

从空格子中均匀随机选取：

```python
empty = np.flatnonzero(board == EMPTY)
idx = self.np_random.choice(empty)
```

保证食物不会落在蛇身上，无需拒绝采样循环。

若棋盘被蛇填满（无空格），episode 以 `terminated=True` 结束，且 `death_penalty = 0`（视为胜利，不是死亡）。

---

## 9. render

```python
env.render()
```

| `render_mode` | 行为 |
|---|---|
| `None` | 空操作，训练默认 |
| `"human"` | Pygame 窗口 |
| `"rgb_array"` | 返回帧数组，供录制视频 |

渲染逻辑放在 `env/renderer.py`，与 `snake_env.py` 解耦。训练默认不渲染（`AI_DEVELOPMENT_RULES.md` §13）。

---

## 10. 配置 key

算法与训练相关 key 以 `AI_DEVELOPMENT_RULES.md` §12 为准，本文件不重复。

环境额外使用以下 5 个 key：

```text
board_size              默认 10
initial_length          默认 3
max_steps_per_episode   默认 500
initial_head            默认 None（随机）
render_mode             默认 None
```

这五个 key 与算法 key 合并在 `common/config.py` 的同一个 `@dataclass Config` 中，组织、覆盖与存档方式见 `AI_DEVELOPMENT_RULES.md` §12。`initial_head` 的命令行写法为 `--initial_head 4,6`。

---

## 11. 实验输出约定

`EXPERIMENT_PROTOCOL.md` 已规定 run 的命名、产出文件与指标字段（第二、六、九、十节）。本节把它们固化为代码可直接照做的目录与文件约定。

### 目录

```text
results/
├── logs/      每个 run 一个子目录
├── figures/   由脚本生成的图表
└── videos/    Demo 录制

checkpoints/   模型权重
```

### run 目录命名

```text
{experiment}_{algorithm}_{state}_{reward}_seed{seed}_{timestamp}
```

示例：

```text
algorithm_dqn_statev1_sparse_seed42_20261006_1800
```

Debug run 在 `experiment` 前加 `debug`，与正式实验区分（`EXPERIMENT_PROTOCOL.md` 第二节）：

```text
debug_state_dqn_statev1_sparse_seed42_20261006_1800
```

### run 目录内容

| 文件 | 内容 | 必需 |
|---|---|---|
| `config.json` | 该 run 的完整配置 | 是 |
| `metrics.csv` | 逐步指标 | 是 |
| `summary.json` | 汇总指标 | 是 |
| `checkpoint.pt` | 模型权重 | 是 |
| `train.log` | 训练日志 | 否 |

### `metrics.csv` 列

```text
episode
episode_return
score
episode_length
epsilon
loss
global_step
```

### `summary.json` 字段

```text
mean_score
std_score
max_score
mean_return
mean_episode_length
```

### 覆盖保护

每次 run 写入**新建**目录，不得复用已存在的 run 目录。正式实验数据不得被后续 debug run 覆盖。

---

## 12. Agent API

Stage 0 冻结。DQN / Double DQN / Dueling DQN 共用同一接口，差异只放在网络结构、target 计算与算法特有配置（`AI_DEVELOPMENT_RULES.md` §10）。

本节把 §10 的推荐接口细化为明确签名。B 实现时如发现签名需要调整，按 §20 流程变更。

### 构造

```python
agent = DQNAgent(state_dim, n_actions, config)
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `state_dim` | `int` | 状态维度，取自 `env.state_dim`（V1 为 11） |
| `n_actions` | `int` | 动作数，取自 `env.n_actions`（3） |
| `config` | `common.config.Config` | 超参数 |

### 方法

```python
action = agent.select_action(state, training=True)
loss = agent.update(batch)
agent.save(path)
agent.load(path)
```

| 方法 | 返回 | 说明 |
|---|---|---|
| `select_action(state, training=True)` | `int` | 取值 ∈ {0, 1, 2}。`training=True` 时按 ε-greedy 探索；`training=False` 时纯贪心，**评估阶段必须用 `False`**（`EXPERIMENT_PROTOCOL.md` 第五节） |
| `update(batch)` | `float \| None` | 反向传播一次，返回 loss。Replay Buffer 未达 `min_buffer_size` 时返回 `None` 且不更新 |
| `save(path)` | `None` | 保存网络权重与 optimizer 状态 |
| `load(path)` | `None` | 加载并覆盖当前状态 |

Replay Buffer 由调用方（训练循环）持有，`update` 接收采样好的 batch。

### `batch` 结构

每条转移必须保留 `terminated` 与 `truncated` 两个独立标记：

```python
(state, action, reward, next_state, terminated, truncated)
```

Bellman target：

```python
target = reward + (1 - terminated) * gamma * max_a Q_target(next_state, a)
```

`truncated` **不参与**该式 —— 截断时蛇仍然活着，仍应 bootstrap。把截断当作真终止会让 Q 值被系统性低估（见 §1）。

batch 的具体容器类型（tuple / dict / tensor）由 B 决定。

### 生命周期约束

`terminated or truncated` 为 True 后不得再调用 `select_action`，必须先 `env.reset()`。

### 实现须知

**1. 签名参考实现见 `env/random_agent.py`。**

`RandomAgent` 已按本节实现 `select_action(state, training=True)`，签名与返回类型可直接对照。DQN 的 `select_action` 与它保持同签名，则 `play.py` / `evaluate.py` 把随机策略换成 DQN 时**不需要修改调用代码**。

`RandomAgent` 没有 `save` / `load`：随机策略没有需要持久化的状态。

**2. 禁止硬编码状态维度与动作数。**

网络输入层必须由 `env.state_dim` 决定，输出层由 `env.n_actions` 决定 ——

```python
agent = DQNAgent(env.state_dim, env.n_actions, config)
```

不要写死 `11` 和 `3`。Stage 4 会引入 State V2，其维度与 V1 不同（`env.state_dim` 届时按 `state_mode` 返回对应值）；写死 `11` 的代码在切换 `state_mode` 后会直接抛形状错误，且报错位置离原因很远。

### 责任边界

| 内容 | 负责 |
|---|---|
| `select_action` / `update` / `save` / `load` 的实现 | B（DQN）、C（Double DQN / Dueling DQN） |
| Replay Buffer 类与 batch 容器类型 | B |
| 训练循环中 buffer 的写入与采样时机 | B（`train.py`） |
| `state_dim` / `n_actions` / 5 元组 / 生命周期 | A（`env/`） |

三种算法不得各建独立训练逻辑（`AI_DEVELOPMENT_RULES.md` §10、§13）。

---

## 变更记录

| 日期 | 内容 |
|---|---|
| 10-06 | 初版。Stage 0 冻结 Environment API、动作空间、State V1（11 维）、`info` 字段、seed 控制与默认参数。 |
| 10-07 | 新增第 11 节：实验输出约定（目录、run 命名、产出文件、指标列）。 |
| 10-07 | 第 12 节新增「实现须知」：指向 `env/random_agent.py` 作为签名参考实现；明确禁止硬编码 `state_dim` / `n_actions`（Stage 4 的 State V2 维度与 V1 不同）。 |
| 10-07 | 新增第 12 节：Agent API（构造、方法签名、batch 结构、责任边界）。 |
| 10-07 | 实现前补齐 4 处缺口：§1 增加 `close()` 与生命周期硬失败约定；§4 增加碰撞判定（蛇尾例外）与非法 `state_mode` 行为；§6 增加非法 `reward_mode` 行为；§8 增加 `initial_head` 参数与初始蛇位置规则；§10 key 数由 4 改为 5。 |
