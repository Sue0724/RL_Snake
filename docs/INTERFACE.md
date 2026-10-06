# 接口定义

Stage 0 冻结。本文件定义 Snake-RL 的 Environment API、动作空间、状态表示、`info` 字段、随机种子控制与默认参数。

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

环境提供的只读属性：

```python
env.state_dim   # 11
env.n_actions   # 3
```

**为什么区分 `terminated` 与 `truncated`**：截断（超时）时蛇仍然活着，bootstrap 仍应进行：

```python
target = reward + (1 - terminated) * gamma * max_a Q_target(next_state, a)
```

若把截断视为真终止，`target = reward`，Q 值被系统性低估。

**生命周期**：`terminated or truncated` 为 True 后不应再调用 `step()`，调用方应先 `reset()`。

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

### State V2

Stage 4 定义，在 V1 基础上**追加维度**，不修改 V1 已冻结的 11 维语义。

`state_mode` 取值：`"v1"`（默认）。

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
| `initial_direction` | `right` | 固定 |
| `render_mode` | `None` | `None` / `"human"` / `"rgb_array"` |

这三个数值在正式实验期间不得更改，否则实验不可比。Stage 2 训练后可依据 `metrics.csv` 中 `episode_length` 的分布与 `truncated` 出现频率复核 `max_steps_per_episode` 是否偏小；复核须在正式实验开始前完成。

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

环境额外使用以下 key，同样集中放在 `common/config.py`：

```text
board_size
initial_length
max_steps_per_episode
render_mode
```

---

## 变更记录

| 日期 | 内容 |
|---|---|
| 10-06 | 初版。Stage 0 冻结 Environment API、动作空间、State V1（11 维）、`info` 字段、seed 控制与默认参数。 |
