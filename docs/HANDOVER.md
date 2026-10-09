# 工作交接与后续安排

本文说明 A 已完成的工作、设计取舍、后续分工，以及接续工作时必须知道的事。

**读者**：项目组全体成员（B / C / D）。

**编写时间**：10-07（Stage 1 验收通过、State V2 预定方案写出之后）。文中「当前进度」「待确认事项」会随阶段推进变化，届时请同步更新本文；规范类内容一律以 `docs/INTERFACE.md` 等文档为准。

**本文与其它文档的分工**：

| 想知道 | 看哪里 |
|---|---|
| 接口的**权威定义**（状态每一位是什么、`info` 有哪些字段、Agent 怎么签名） | `docs/INTERFACE.md` |
| 每个阶段**要做什么** | `docs/PROJECT_PLAN.md` |
| 现在**进行到哪**、有什么问题 | `docs/PROJECT_STATUS.md` |
| 实验怎么跑才**公平可复现** | `docs/EXPERIMENT_PROTOCOL.md` |
| 分支怎么开、代码怎么合 | `docs/COLLABORATION_RULES.md` |
| **为什么这么设计**、接下来谁做什么 | 本文 |

本文只讲设计动机与分工，**不重复规范正文**。若本文与上述文档冲突，以规范文档为准。

---

## 一、当前进度

| Stage | 内容 | 状态 | 负责人 |
|---|---|---|---|
| 0 | 工程初始化与接口冻结 | 仅剩「所有成员理解接口」待确认 | 全员 |
| 1 | Snake 环境与状态 | **Passed**（10-07 确认） | A |
| 2 | DQN Baseline | 配置前置已完成，算法待实现（10-09 更新） | B |
| 3 | 统一训练与评估框架 | 未开工 | B 主导，全员确认 |
| 4 | 状态实验 | 未开工（方案已设计） | A |
| 5 | Reward 与探索实验 | 未开工 | D |
| 6 | Double DQN / Dueling DQN | 未开工 | C |
| 7 | 综合实验 | 未开工 | D 主导，全员 |
| 8 | Demo 与课程汇报 | 未开工 | 全员 |

Stage 1 的全部代码与文档已合入 `main`。**从 `main` 开分支即可拿到可运行的环境。**

---

## 二、A 已完成的工作

### 2.1 环境建模

**棋盘与坐标**：`board_size × board_size` 的方格（默认 10×10）。`row` 向下增大，`col` 向右增大。每步蛇头移动一格。

**动作空间：相对动作，3 个**

```text
0 = 直行    1 = 左转 90°    2 = 右转 90°
```

这是本项目的一个关键设计决定。

*为什么不用绝对动作（上/下/左/右）*：绝对动作会产生 180° 反向，需要额外禁用，而且同一策略在不同朝向下学到的东西不能复用——蛇朝上时"按左键"和朝下时"按左键"含义完全不同，网络要分别学四套。相对动作下"左转"在任何朝向下都是同一个语义，**样本效率更高**，且天然不存在反向动作，不需要禁手逻辑。

*代价*：人是按绝对方位思考的，所以键盘控制（`play.py --agent human`）里 `A` 键是"相对当前朝向左转"而不是"向左走"。首次使用需要适应，脚本里已印出提示。

**状态表示的基础**：整个状态以**蛇头朝向为"前方"**来组织（详见 2.2）。

**蛇的表示**：内部用 `body`（`deque`，`[0]` 是蛇头）+ `occupied`（`set`）两个结构。两者只在 `_place_snake` 与 `_advance` 两个函数里同时改动，避免出现"两个结构不同步"这类难查的 bug。

**碰撞判定**：

```text
落点出界                     → 碰撞
落点在蛇身（不含蛇尾）        → 碰撞
落点 == 蛇尾                 → 不碰撞
```

蛇尾是唯一的例外——它在同一步会腾出格子，所以落进蛇尾是合法的。"吃到食物时尾巴不动"不需要单独分支：吃到食物意味着落点等于食物，而食物永远生成在空格子，两者不可能同时成立。

**这条规则同时被 `step()` 和状态里的 `danger_*` 使用，是同一个函数。** 如果危险位用"含蛇尾"的保守版本，状态就会把"其实能走"的方向标成危险，等于给网络喂错标签。测试里有一条专门做"`danger_*` 与真实 `step()` 结果逐动作比对"。

**食物生成**：从所有空格子中均匀随机选一个。不用拒绝采样循环——调用前棋盘必然有空格。**食物永远不会落在蛇身上。**

**episode 生命周期**：

```text
terminated = True   撞墙或撞自身（真终止）
truncated  = True   步数达到上限（默认 500）但蛇还活着
```

**这两者必须分开**，是本项目最容易出错的一点。截断时蛇仍然活着，Bellman target 仍应 bootstrap：

```python
target = reward + (1 - terminated) * gamma * max_a Q_target(next_state, a)
```

若把截断当作真终止，`target = reward`，Q 值会被系统性低估。**写 DQN 时请务必核对这一条**，`QUICKSTART.md` 里也单独标了警示。

**胜利条件**：棋盘被蛇填满时 `terminated = True`，视为胜利而非死亡。

**奖励（当前 `reward_mode="sparse"`）**：

```text
吃到食物   +10.0
死亡       -10.0
其余        0.0
```

`step_reward` 与 `distance_reward` 两个分项已经在 `info` 里预留了字段，当前恒为 0，由 Stage 5 填充。

### 2.2 状态设计 V1（11 维，已冻结）

完整索引表见 `docs/INTERFACE.md` §4。这里讲**为什么这么切**：

```text
索引 0-2    danger_straight / danger_left / danger_right   三个动作各自会不会撞
索引 3-6    moving_up/down/left/right                     当前朝向（one-hot）
索引 7-10   food_up/down/left/right                       食物相对蛇头的方向
```

三段分别回答三个问题：**「我能往哪走」「我在朝哪」「食物在哪个方向」。** 这是贪吃蛇状态表示的最小可用集。

几个具体决定：

- **`danger_*` 只有 3 个而不是 4 个**：因为动作空间只有 3 个，三个危险位正好一一对应"执行该动作后会不会死"。第 4 个方向（后方）做不到，不需要。
- **`moving_*` 用 one-hot**：朝向是 4 选 1 的类别量，用 one-hot 而非单个整数（0/1/2/3），避免网络把"上"和"下"当成数值上接近的方向。
- **`food_*` 不互斥**：食物在左上方时 `food_up` 和 `food_left` 同时为 1。这是方向位，不是类别量。
- **状态里不含蛇身坐标**：11 维是定长的、与蛇长无关；把蛇身坐标塞进去会让维度随长度变化，网络无法处理。

**V1 的两个结构性盲区（这正是 State V2 要解决的）**：

1. **看不见蛇身的形状。** 只有 3 个危险位，能回答"下一步会不会死"，但无法回答"走这一步之后会不会把自己围死"。蛇变长后失败的主因是自围，V1 没有任何依据规避。
2. **看不见食物的距离。** `food_*` 只给方向位，网络无从区分"距离 1 格"和"距离 15 格"，接近食物途中缺少紧迫感信号，容易绕圈。

### 2.3 工程实现

| 文件 | 作用 | 说明 |
|---|---|---|
| `env/snake_env.py` | 环境逻辑 | 不依赖 pygame，训练时不加载渲染代码 |
| `env/renderer.py` | pygame 渲染 | `human` 建窗口 / `rgb_array` 离屏；`render_mode=None` 时完全不导入 |
| `env/random_agent.py` | 随机策略 | **`select_action` 签名已对齐 Agent API，可作为 DQN 的参考实现** |
| `play.py` | 可视化跑一局 | `--agent random` / `--agent human`，也可用于演示与人工验证 |
| `tests/` | 54 项 pytest | 环境 41 / 渲染 5 / 随机策略 3 / play 5 |

**渲染是分层的**：`snake_env.py` 完全不 import pygame，只有在 `render_mode` 非 None 时才惰性导入 `renderer`。这样训练、评估、批量实验都不会加载渲染相关代码。

**`RandomAgent` 的签名值得 B 参考**：它已经实现了 `select_action(state, training=True)`，与 `docs/INTERFACE.md` §12 定义的 Agent API 一致。DQN 只要对齐这个签名，`play.py` / `evaluate.py` 就不用改调用代码。

### 2.4 过程中修的两个问题（其他人也可能撞上）

**① 中文输入法吞键，导致 `play.py --agent human` 键盘完全无响应**

中文输入法激活时，Windows 发出的 `WM_KEYDOWN` 里 `wParam` 是 `VK_PROCESSKEY` 而不是真实虚拟键码，于是 pygame 的 `event.key` 永远匹配不上 `K_w` / `K_a` / `K_s` / `K_d`，看起来像"程序没响应按键"。

修复：建窗后调用 `pygame.key.stop_text_input()` 关闭输入法组合态。

*教训*：这个问题**无法用自动测试覆盖**（需要真人按键），是靠实际游玩发现并确认的。如果你以后改了渲染或事件处理，需要人工回归一次。

**② `play.py --agent random` 每次跑出完全相同的轨迹**

`Config.seed` 默认 42，同时喂给了环境和随机策略，所以每次演示都是同一个起点、同一条路径、同一种死法。

修复：`play.py` 不传 `--seed` 时随机取一个并打印（附复现命令），传了则原样使用。**这个行为只作用于 `play.py`**——`train.py` / `evaluate.py` 仍严格受 `Config.seed` 控制，实验可复现性不受影响。

---

## 三、State V2 预定方案（**待团队确认**）

V2 已在 `docs/INTERFACE.md` §4 写出完整规格，状态为 **预定方案、尚未冻结**。

**一句话摘要**：V2 = V1 的 11 维 + `food_distance`（归一化 Manhattan 距离）+ `local_ring`（蛇头周围 8 格占用环），共 **20 维**，通过 `--state_mode v2` 启用。追加的两类信息正对应 2.2 节说的两个盲区。

**需要团队确认的点**：

- **方案本身**。若认为"一次加两类信息"导致结果无法归因，可改为只加其中一类——这是最可能的修改点，改动成本低（只改 `docs/INTERFACE.md` §4）。
- **对 C 的影响**：Stage 6 的网络输入层会从 11 变 20。**只要按 5.2 节第 1 条不硬编码维度，就不需要改代码。**
- **对 B 的影响**：Stage 3 的 `train.py` 需要支持 `--state_mode` 参数（`Config` 里已有该字段，环境侧也已预留分支）。

**确认方式**：按 `docs/AI_DEVELOPMENT_RULES.md` §20 走变更流程，在 Stage 4 开工前定稿。

---

## 四、后续工作安排

### 4.1 责任边界

| 成员 | 主要负责 |
|---|---|
| A | `env/snake_env.py`、renderer、状态表示、`state_experiment` |
| B | `algorithms/dqn.py`、Replay Buffer、Target Network、DQN baseline、统一训练框架 |
| C | `algorithms/double_dqn.py`、`algorithms/dueling_dqn.py`、`algorithm_experiment` |
| D | `reward_experiment`、`hyperparameter_experiment`、汇总分析、最终对比 |

**「主要负责」不等于其他人不可修改。跨责任区修改前应说明原因**（`docs/COLLABORATION_RULES.md`）。

### 4.2 B：Stage 2 + Stage 3

Stage 2 与 Stage 3 是全项目最重的连续两块，也是所有人的前置依赖。

**配置前置已完成（10-09）**：经用户确认，epsilon 采用按训练环境步进行的指数衰减，默认值 `1.0 / 0.05 / 0.9999`，跨局延续，评估不衰减。完整执行规则以 `docs/AI_DEVELOPMENT_RULES.md` §12 为准。B 接下来据此实现 DQN；D 在 Stage 5 的探索实验沿用该基线规格。

**开工前请读两处**：

- `docs/INTERFACE.md` §12「实现须知」——签名参考实现 + 禁止硬编码维度
- `docs/AI_DEVELOPMENT_RULES.md` §12——已冻结的 `epsilon_decay` 执行规则

Stage 3 的验收项里包含 `state_mode` 可配置，与 State V2 相关。

### 4.3 C：Stage 6

Stage 6 在 Stage 3 之后。要做的两件事与已有设计的关系：

- **Double DQN**：Online Network 选动作、Target Network 评估，两者都来自 Stage 2，不要重写。
- **Dueling DQN**：共享特征层 + Value / Advantage 双流 + 聚合公式。

**唯一的接口约束**：三种算法必须能统一切换、统一评估，**不得各自建立独立训练逻辑**（`docs/AI_DEVELOPMENT_RULES.md` §10 / §13，Stage 6 验收项里有"不存在重复训练系统"一条）。

**受 State V2 影响的唯一一点**：网络输入层维度。按 5.2 节第 1 条写就不会有问题。

### 4.4 D：Stage 5 + Stage 7

**Stage 5（Reward 与探索）**：`docs/PROJECT_PLAN.md` 中本阶段负责人是 D。

Reward Shaping 的实现落在 `env/snake_env.py` 的 `_compute_reward()`——那是 A 的责任区，但**按协作规则，跨责任区修改只需说明原因即可，不需要 A 参与实现**。`distance_reward` 与 `step_reward` 两个分项字段已经预留好，当前恒为 0。D 自行实现并在提交信息里说明即可，A 事后 review。

*本阶段最大的风险*：Reward Shaping 最容易产生"Return 很高但实际不会吃食物"的伪改进。**必须同时观察 Score**，不能只看 Return。

**Stage 7（综合实验）**：D 主导，全员参与。实验矩阵模板见 `docs/EXPERIMENT_PROTOCOL.md` 第十四节。

### 4.5 A：Stage 4

前置依赖：Stage 2（DQN）+ Stage 3（`train.py` / `evaluate.py` 统一框架）。

**为什么必须等**：Stage 4 的验收项要求"相同训练预算""至少 3 个 seed""原始日志保存""曲线生成""汇总指标生成"，这些都需要统一框架的产出。而且 `docs/AI_DEVELOPMENT_RULES.md` §13 禁止无必要地创建 `train_dqn.py` 之类的脚本，所以 A 不能自己写一套训练脚本绕过去——那会造成重复训练系统。

实验设计**已经写好了**，不需要重新设计：`docs/EXPERIMENT_PROTOCOL.md` 第十四节的矩阵里 **E2 就是状态实验**（DQN / V1 vs V2 / Sparse / Default 探索 / seeds 42-44），第三节定了种子集合，第四节定了预算口径（优先用 environment steps）。

A 到 Stage 4 时要做的：实现 V2、跑 E2、出曲线与汇总、写状态设计分析。

### 4.6 阶段之间的依赖

```text
Stage 1 (环境) ──→ Stage 2 (DQN) ──→ Stage 3 (统一框架) ──┬─→ Stage 4 (状态)
                                                          ├─→ Stage 5 (Reward)
                                                          └─→ Stage 6 (算法)
                                                                    ↓
                                                        Stage 7 (综合) ──→ Stage 8 (汇报)
```

**Stage 3 是所有人的瓶颈。** 它完成之前，Stage 4 / 5 / 6 都无法开始。

---

## 五、接续工作须知

### 5.1 从哪里开始

```bash
git checkout main
git pull
git checkout -b feature/dqn        # 换成自己的分支名
```

分支名沿用 `docs/COLLABORATION_RULES.md` 已列出的那套。**不要从其他人的 feature 分支开分支**——会把对方的历史一并继承，后续理不清依赖关系。

阶段验收通过后合回 `main`。完整流程见 `docs/COLLABORATION_RULES.md`「Git 工作流」。

### 5.2 三条不能踩的线

**① 不要硬编码状态维度与动作数**

```python
agent = DQNAgent(env.state_dim, env.n_actions, config)   # 对
agent = DQNAgent(11, 3, config)                          # 错
```

Stage 4 会引入 State V2（20 维）。写死 `11` 的代码在切换 `state_mode` 后会直接抛形状错误，**而且报错位置离原因很远**，很难查。

**② `epsilon_decay` 必须按冻结语义实现**

见 4.2 节。默认方案已于 10-09 冻结；实现不能改成按 episode 或网络更新次数衰减，后续规格变更仍按开发规范 §20 执行。

**③ 改接口要走变更流程**

Environment API、Agent API、Config key、metrics 字段、实验输出格式都已冻结。确需修改时按 `docs/AI_DEVELOPMENT_RULES.md` §20：说明原因 → 列出影响文件 → 给出方案 → 等待确认 → 更新全部调用方与文档 → 完成集成测试 → 在 `PROJECT_STATUS.md` 记录。

### 5.3 已知遗留问题

| 问题 | 影响 | 处理 |
|---|---|---|
| 随机初始蛇头可能落在边缘，约 3.3% 的开局第一步即撞墙 | 演示观感略差；**对训练与实验无影响** | 属合法随机结果，非缺陷。留待 Stage 8 前再议，改动会触及 Stage 1 已冻结行为与既有测试 |
| `human` 模式关闭输入法的效果无法自动测试 | 回归风险由人工验证承担 | 改了渲染或事件处理时人工回归一次 |
| 初始蛇头允许贴边带来一个副作用 | `--seed` 抽到最右列开局时整局只有 1 步 | 同上，非缺陷 |

### 5.4 何时更新文档

- 完成实际操作后追加 `memory.md`（规则见 `docs/AI_DEVELOPMENT_RULES.md` §21，注意「追加时回头核对」）
- 必要时更新 `docs/PROJECT_STATUS.md`
- 阶段验收后更新 `docs/STAGE_CHECKLIST.md`

---

## 六、确认事项

| # | 事项 | 谁定 | 什么时候 |
|---|---|---|---|
| 1 | `epsilon_decay` 的衰减语义与默认取值 | B | 已于 10-09 经用户确认冻结 |
| 2 | State V2 方案（`docs/INTERFACE.md` §4） | 团队 | Stage 4 开工前 |
| 3 | Stage 0 的「所有成员理解接口」 | 全员 | 不阻塞任何阶段 |

第 3 项的确认方式很简单：各自读一遍 `docs/INTERFACE.md` 与 `QUICKSTART.md`，有问题提出来；没有则视为确认。

---

## 七、参考文档索引

```text
docs/INTERFACE.md            接口权威定义（环境 / 动作 / 状态 / info / 配置 / Agent）
docs/PROJECT_PLAN.md         每个阶段要做什么
docs/PROJECT_STATUS.md       当前进度与问题
docs/STAGE_CHECKLIST.md      每个阶段的验收清单
docs/EXPERIMENT_PROTOCOL.md  实验规范（种子、预算、指标、命名、绘图、实验矩阵）
docs/COLLABORATION_RULES.md  责任边界、Git 工作流、冲突处理
docs/AI_DEVELOPMENT_RULES.md 开发规范（阶段控制、配置、日志、禁止事项）
QUICKSTART.md                接口速查页
```
