# AI 开发统一规范

## 1. 文档目的

本文件是 Snake-RL 项目中 Codex、Claude Code 以及其他 AI 编程助手共同遵守的唯一核心开发规范。

`codex.md` 与 `claude.md` 不再分别定义不同的工程规则。两者只负责说明对应工具在进入项目时应该如何加载本规范。

如其他文档与本文件在 AI 开发流程上存在冲突，以本文件为准；如实验设计存在冲突，以 `docs/EXPERIMENT_PROTOCOL.md` 为准；如阶段目标存在冲突，以 `docs/PROJECT_PLAN.md` 与 `docs/STAGE_CHECKLIST.md` 为准。

---

## 2. 项目目标

项目名称：

`Snake-RL`

项目主题：

**基于深度强化学习的贪吃蛇智能体设计与实验研究**

项目最终不是只完成一个可运行 Demo，而是形成：

- 可运行的 Snake 强化学习环境
- DQN 基线
- Double DQN
- Dueling DQN
- 状态设计实验
- Reward Shaping 实验
- 探索 / 超参数实验
- 统一训练与评估框架
- 可复现实验结果
- 可视化 Demo
- 可用于课程汇报的实验结论

核心研究链：

```text
Snake Environment
        ↓
State Representation
        ↓
Reward Design
        ↓
DQN Baseline
        ↓
Double DQN / Dueling DQN
        ↓
Unified Experiments
        ↓
Ablation & Comparison
        ↓
Visual Demo
```

---

## 3. 每次开始工作前必须阅读

按以下顺序：

1. `README.md`
2. `docs/PROJECT_STATUS.md`
3. `memory.md`
4. `docs/PROJECT_PLAN.md`
5. `docs/STAGE_CHECKLIST.md`
6. `docs/EXPERIMENT_PROTOCOL.md`
7. `docs/COLLABORATION_RULES.md`
8. 当前任务涉及的代码

必须先确认：

- 当前处于哪个 Stage
- 当前 Stage 已完成什么
- 当前 Stage 还缺什么
- 是否已经存在相同或类似实现
- 本次修改是否会影响既有接口或实验结果

不得假设项目当前状态。

---

## 4. 原有名称不得修改

以下原有路径和名称必须保留：

```text
env/snake_env.py

algorithms/dqn.py
algorithms/double_dqn.py
algorithms/dueling_dqn.py

experiments/state_experiment/
experiments/reward_experiment/
experiments/hyperparameter_experiment/
experiments/algorithm_experiment/

models/
results/
play.py
```

允许新增合理辅助模块，例如：

```text
env/renderer.py
algorithms/networks.py
common/
checkpoints/
docs/
train.py
evaluate.py
```

但不得为了“更规范”“更漂亮”而擅自重命名原有结构。

---

## 5. 修改前必须先询问

除非用户在当前指令中明确说“直接修改”“直接执行”“无需询问”，否则任何代码或项目文件修改前都必须先说明并等待用户确认。

回复格式应尽量简洁：

```text
准备修改：
- ...

原因：
- ...

涉及文件：
- ...

推荐方案：
- ...

备选方案：
- ...（仅在确有必要时提供）

是否按推荐方案执行？
```

要求：

- 推荐方案优先给出一个。
- 备选方案最多 2 个。
- 不要为了凑选项而给出低质量方案。
- 未得到确认前，不得开始修改代码或项目文件。

---

## 6. 一次只推进当前阶段

除非用户明确要求跨阶段开发，否则不得提前实现后续阶段的大量内容。

工作流程：

```text
确认当前 Stage
    ↓
提出本次修改方案
    ↓
等待用户确认
    ↓
实施
    ↓
运行测试
    ↓
追加 memory.md 操作记录
    ↓
对照验收清单
    ↓
更新 PROJECT_STATUS
    ↓
汇报结果与问题
    ↓
询问是否进入下一步 / 下一 Stage
```

当前 Stage 未通过验收，不得主动进入下一 Stage。

---

## 7. 阶段完成后必须再次询问

一个 Stage 完成后，必须：

1. 运行实际测试。
2. 对照 `docs/STAGE_CHECKLIST.md`。
3. 标记已满足与未满足项。
4. 追加 `memory.md` 操作记录。
5. 更新 `docs/PROJECT_STATUS.md`。
6. 列出遗留问题。
7. 明确判断当前 Stage 是否通过。
8. 询问用户是否进入下一 Stage。

禁止自动继续下一阶段。

---

## 8. 禁止伪造运行与实验结果

不得在没有实际执行的情况下声称：

- 环境运行正常
- 测试通过
- 模型训练成功
- 算法已经收敛
- Double DQN 优于 DQN
- Reward Shaping 有效
- 性能提高
- 实验完成

如果没有执行，应写：

```text
未运行验证
```

如果执行失败，应写：

```text
验证失败
```

如果只有部分验证，应写：

```text
部分通过
```

不得使用随机生成数据、手工数据或虚构曲线冒充实验结果。

---

## 9. 环境设计原则

`env/snake_env.py` 应保持环境与算法解耦。

接口已冻结，以 `docs/INTERFACE.md` 为准：

```python
env = SnakeEnv(config)

state, info = env.reset(seed=seed)
next_state, reward, terminated, truncated, info = env.step(action)
env.render()
```

采用 Gymnasium 风格 5 元组返回值。`terminated` 表示撞墙或撞自身，`truncated` 表示达到 `max_steps_per_episode`。

两者必须区分：截断时蛇仍然活着，bootstrap 仍应进行：

```python
target = reward + (1 - terminated) * gamma * max_a Q_target(next_state, a)
```

若把截断当作真终止，`target = reward`，Q 值被系统性低估。

冻结后如需变更，按 §20 执行。

环境应支持：

- 固定随机种子
- 无渲染训练
- 可视化 Demo
- 不同 state mode
- 不同 reward mode

状态实验与奖励实验不能通过复制多份 Snake 环境实现。

---

## 10. Agent 统一接口

DQN、Double DQN、Dueling DQN 应尽量共享接口。

推荐：

```python
agent.select_action(state, training=True)
agent.update(batch)
agent.save(path)
agent.load(path)
```

算法差异主要放在：

- 网络结构
- target 计算
- 必要的算法特有配置

禁止为三个算法复制三套完整训练逻辑。

---

## 11. DQN 必须包含的核心模块

标准 DQN 至少应具备：

- Online Q Network
- Target Network
- Replay Buffer
- epsilon-greedy
- Bellman Target
- mini-batch training
- optimizer
- target update
- checkpoint save/load

Double DQN 必须满足：

```text
Online Network：选择下一动作
Target Network：评估该动作
```

Dueling DQN 必须包含：

```text
shared feature
  ├─ value stream
  └─ advantage stream
```

推荐聚合：

```text
Q(s,a) = V(s) + A(s,a) - mean_a A(s,a)
```

---

## 12. 配置管理

超参数必须集中管理，禁止大量散落在源码中的魔法数字。

至少应包含：

```text
seed
device
algorithm
state_mode
reward_mode

gamma
learning_rate
batch_size
buffer_size
min_buffer_size

target_update_interval

epsilon_start
epsilon_end
epsilon_decay

num_episodes
max_steps_per_episode

hidden_dim
```

实验中一次只改变当前研究变量。

### 待冻结：`epsilon_decay` 的衰减语义

**状态：未定义，进入 Stage 2 前必须由 B 选定并写回本节。** 本表只列参数名与默认值，没有说明 `epsilon_decay` 是「每 step 衰减一次」还是「每 episode 衰减一次」。两种语义在当前默认值下相差约 50 倍，实现前必须二选一，否则 D 在 Stage 5 做探索策略对比时，自变量无法说明。

当前取值（`common/config.py`）：`epsilon_start=1.0`、`epsilon_end=0.05`、`epsilon_decay=0.995`、`num_episodes=1000`、`max_steps_per_episode=500`。

从 `epsilon_start` 衰减到 `epsilon_end` 所需次数（`ln(0.05)/ln(decay)`）：

| 方案 | 需要次数 | 换算成 episode | 判断 |
|---|---|---|---|
| 每 step，`decay=0.995` | 598 步 | ≈1.2 个 episode | 太快，探索基本没发生 |
| 每 episode，`decay=0.995` | 598 episode | 598 / 1000 | 数值合理 |
| **每 step，`decay=0.9999`** | **29,956 步** | **≈100～300 episode** | **推荐** |

**推荐：每 step 衰减，同时把默认值 `0.995` 改为 `0.9999`。**

理由：episode 长度由智能体当前水平决定——训练初期几步就撞死，后期一局几百步。若按 episode 衰减，同样是乘 0.995，早期消耗的总步数远少于后期，**探索预算因此变成了智能体水平的函数**。Stage 5 要比较「不同 epsilon 衰减策略」，自变量必须是确定量。按 step 衰减与智能体行为无关，可直接由 `num_episodes × 平均 episode 长度` 推算。

选定后需要同步修改的位置：本节、`common/config.py` 的 `Config` 默认值、`docs/INTERFACE.md`（若其中引用了该参数）。改动属于规格变更，按本节要求走变更流程。

**分工提示**：B 在 Stage 2 实现 epsilon-greedy 时必须依此表实现；D 在 Stage 5 的探索策略实验依赖此语义。B 若对推荐有异议，应在实现前提出，不要默默选择。

### 组织形式

配置集中在 `common/config.py` 的 `@dataclass Config` 中，环境侧 4 个 key（见 `docs/INTERFACE.md` §10）与上表算法 key 合并在同一个类内。

新增字段只需在 `Config` 中加一行，命令行参数自动生成，不需要另行维护参数表。

### 覆盖方式

```python
from common.config import parse_args

cfg = parse_args()      # 只覆盖显式传入的参数
```

```bash
python train.py --algorithm dqn --seed 42
```

一次只改一个研究变量，正好对应一次一个命令行参数。

### 存档方式

每个 run 保存完整配置：

```python
import dataclasses
import json

with open(run_dir / "config.json", "w", encoding="utf-8") as f:
    json.dump(dataclasses.asdict(cfg), f, indent=2, ensure_ascii=False)
```

### 不使用 YAML 配置文件

`EXPERIMENT_PROTOCOL.md` 第十节要求的 `config.json` 是每个 run 的输出记录，不是输入。引入 YAML 会多一个依赖、多一个「文件与命令行谁优先」的歧义，并产生两个真相来源。

---

## 13. 统一训练与评估

训练入口优先统一为：

```text
train.py
```

评估入口优先统一为：

```text
evaluate.py
```

展示入口保留：

```text
play.py
```

不得无必要创建：

```text
train_dqn.py
train_double_dqn.py
train_dueling_dqn.py
```

训练默认：

```text
render = False
```

评估默认：

```text
exploration = False
network_update = False
replay_write = False
```

---

## 14. 日志要求

每次正式实验至少记录：

```text
run_id
algorithm
seed
state_mode
reward_mode

episode
global_step
episode_return
score
episode_length

epsilon
loss
```

可选：

```text
mean_q_value
max_q_value
wall_clock_time
```

Reward Shaping 实验推荐额外记录：

```text
food_reward
death_penalty
distance_reward
step_reward
```

不能只看 Return，还必须同时观察真实 Score。

---

## 15. 正式实验要求

正式实验必须遵守 `docs/EXPERIMENT_PROTOCOL.md`。

最低要求：

- 同组实验控制变量
- 至少 3 个随机种子
- 保存 config
- 保存原始 metrics
- 保存 summary
- 保存必要 checkpoint
- 结果图可由脚本重新生成

推荐 seeds：

```text
42
43
44
```

条件允许时：

```text
42
43
44
45
46
```

禁止只展示表现最好的 seed。

---

## 16. 调试顺序

训练效果异常时，优先按以下顺序排查：

1. 环境逻辑
2. 状态数值与维度
3. 动作映射
4. reward
5. terminated / truncated 条件
6. Replay Buffer
7. tensor shape
8. Bellman target
9. Target Network 更新
10. optimizer
11. epsilon
12. 超参数

不要一开始就通过反复调学习率掩盖实现错误。

---

## 17. 修改后的测试要求

### 修改环境后

至少检查：

- reset
- step
- 碰墙
- 撞自身
- 食物生成
- 吃食物增长
- terminated / truncated
- seed
- 无渲染模式
- Random Agent smoke test

### 修改算法后

至少检查：

- tensor shape
- forward
- loss
- backward
- optimizer step
- Replay Buffer sample
- Target Network update
- save/load

### 修改训练 / 实验脚本后

至少检查：

- CLI / config
- seed
- 日志保存
- checkpoint
- 输出路径
- 多次运行是否错误覆盖历史结果

---

## 18. 代码质量原则

优先级：

1. 正确
2. 可复现
3. 可测试
4. 易读
5. 易维护
6. 性能

避免：

- 过度抽象
- 无必要设计模式
- 超大类
- 隐式全局状态
- 大量重复代码
- 魔法数字
- 一个函数同时负责环境、训练、日志、绘图

---

## 19. 实验公平性

例如比较：

```text
DQN
Double DQN
Dueling DQN
```

应尽量保持：

- 相同 state
- 相同 reward
- 相同训练预算
- 相同 seed 集合
- 相同 batch size
- 相同 gamma
- 相同 optimizer
- 相同 learning rate
- 相同 Replay Buffer
- 相同 evaluation protocol

如果网络结构导致参数量无法完全一致，必须在报告中说明。

---

## 20. 修改现有接口时

修改 Environment API、Agent API、Config key、metrics 字段等核心接口时，必须先：

1. 说明修改原因。
2. 列出影响文件。
3. 给出推荐方案。
4. 等待用户确认。

修改后必须：

1. 更新全部调用方。
2. 更新文档。
3. 进行集成测试。
4. 在 `PROJECT_STATUS.md` 记录。

---

## 21. 项目操作日志 `memory.md`

`memory.md` 记录“做过什么、结果如何”，按日期持续追加，不覆盖历史。

项目当前进行到哪一步、当前问题与下一步，由 `docs/PROJECT_STATUS.md` 负责，不写入本日志。

### 需要记录

每完成一个与项目紧密相关的实际操作后，必须追加一条记录。包括但不限于：

- 修改代码
- 修改项目文档
- 修改目录或接口
- 修改环境、奖励、状态或算法
- 执行测试
- 执行训练或评估
- 执行正式实验
- 生成模型、图表或结果
- 修复 Bug
- Git 合并、回滚等重要版本操作
- 阶段验收或阶段状态变化

### 不需要记录

- 单纯询问强化学习概念
- 询问“某个算法是什么”
- 尚未执行的建议或设想
- 纯聊天
- 未对项目产生实际变更的方案讨论
- 重复解释已存在的项目内容

### 字段与格式

每条记录至少必须包含，不得省略：

```text
日期
操作内容
结果
```

推荐同时记录：

```text
操作类型
涉及文件
执行 / 验证
关键结果
发现的问题
后续影响
```

日期格式统一为：

```text
MM-DD
```

同一天的所有操作合并到同一条记录，后续操作直接追加到该记录的对应字段下，不新建日期标题。

不得伪造日期。无法可靠获取日期时，应注明：

```text
日期：未能可靠获取
```

### 日志规则

- 只追加，不覆盖历史。
- **追加时回头核对**：同一天追加新内容前，先扫一遍该条记录已有的「发现的问题」与「后续影响」，把被本次操作推翻或已解决的句子**就地改掉**，不要只在下面追加一条新说明。
  - 「发现的问题」与「后续影响」描述的是**当前状态**，不是历史；留着已被推翻的结论，会让后来的读者（包括下一位接手者的 AI 助手）据此判断错误。
  - 例：先写了「Stage 1 结论 `Passed`（待成员确认）」，成员确认后就回头把那一句改成已确认，而不是在下面再补一条「已确认」。
  - 反例对照：「操作内容」按时间顺序记录「当时做了什么」，其中的阶段性结论（如「结论 `Passed`（待确认）」）**属于合法历史**，若后续有操作改写了它，只要在「操作内容」里补一条说明即可，不必回头改。这条规则约束的是「发现的问题」与「后续影响」两段。
- 失败也要记录。
- 未测试必须写 `Not Tested`。
- 部分通过必须写 `Partial`。
- 不得把计划写成已完成。
- 不记录 commit hash（`git log` 已是权威记录），只记操作内容、结果与产出物路径。
- 一次连续操作可合并成一条记录，但必须能看清修改内容和结果。
- 与 Bug 修复相关的记录，应包含问题现象、修改内容和修复结果。
- 正式实验应记录 run_id、seed、主要配置和输出路径。
- 记录应简洁，避免写成长篇开发日记。

### 记录模板

```text
## MM-DD

操作类型：Code / Docs / Test / Train / Evaluate / Experiment / Fix / Git / Stage / Other
结果：Passed / Failed / Partial / Not Tested

操作内容：
- ...

涉及文件：
- ...

执行 / 验证：
- ...

关键结果：
- ...

发现的问题：
- ...

后续影响：
- ...
```

没有内容的字段可写 `无` 或直接省略，但日期、操作内容、结果三项不得省略。

### 正式实验记录补充模板

```text
## MM-DD

操作类型：Experiment
结果：Passed / Failed / Partial

实验：
- run_id: ...
- algorithm: ...
- state_mode: ...
- reward_mode: ...
- seed: ...
- training_budget: ...

输出：
- config: ...
- metrics: ...
- summary: ...
- checkpoint: ...

关键指标：
- mean_score: ...
- max_score: ...
- mean_return: ...

备注：
- ...
```

项目操作完成后的顺序应为：

```text
完成实际操作
    ↓
运行必要验证
    ↓
追加 memory.md
    ↓
必要时更新 PROJECT_STATUS.md
    ↓
向用户汇报
```

---

## 22. 项目状态维护

完成每次已批准的开发任务后，更新：

`docs/PROJECT_STATUS.md`

只记录有效内容：

```text
完成：
- ...

测试：
- ...

结果：
- Passed / Failed / Partial

发现问题：
- ...

下一步：
- ...
```

不要写冗长开发日记。

---

## 23. 每次任务完成后的固定汇报格式

```text
本次完成：
- ...

修改文件：
- ...

实际测试：
- 命令 / 测试内容：
  ...
- 结果：
  Passed / Failed / Partial

当前阶段验收：
- 已满足：
  - ...
- 未满足：
  - ...

发现的问题：
- ...

建议：
- 推荐：...
- 备选：...（确有必要时）

是否可以继续下一步：
- 是 / 否
- 原因：...
```

如果下一步涉及新的修改，必须再次等待用户确认。

---

## 24. 禁止事项

- 不得擅自重命名原有核心路径。
- 不得未经确认进行代码或项目文件修改。
- 不得未经确认跨 Stage。
- 不得伪造测试结果。
- 不得伪造训练曲线。
- 不得删除已有实验结果。
- 不得只挑最好看的 seed。
- 不得为了证明算法有效而改变评价口径。
- 不得绕过失败测试。
- 不得把实时渲染作为默认训练方式。
- 不得在不同算法中偷偷使用不同指标。
- 不得看到单条曲线上升就直接宣称“收敛”。

---

## 25. 核心判断标准

“代码写完”不等于“任务完成”。

“能运行”不等于“阶段完成”。

“Return 上升”不等于“策略更好”。

“单个 seed 更高”不等于“算法更优”。

每个阶段最终都必须回答：

```text
是否正确？
是否实际验证？
是否可复现？
是否能公平比较？
是否能解释？
是否有利于最终课程汇报？
```
