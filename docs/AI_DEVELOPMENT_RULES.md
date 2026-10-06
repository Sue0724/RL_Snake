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

推荐统一接口：

```python
state = env.reset(seed=seed)
next_state, reward, done, info = env.step(action)
env.render()
```

如果后续决定采用 Gymnasium 风格返回值，可以修改，但必须：

- 先说明影响
- 获得用户确认
- 一次性同步所有调用位置
- 更新相关文档
- 重新进行集成测试

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
5. done 条件
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
- done
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

每完成一个与项目紧密相关的实际操作后，必须在项目根目录的：

`memory.md`

中追加一条操作记录。

这里的“实际操作”包括但不限于：

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

普通咨询、理论解释、未执行的建议和纯方案讨论不需要记录。

每条记录至少必须包含：

```text
时间
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

时间格式统一为：

```text
YYYY-MM-DD HH:MM +08:00
```

日志规则：

- 只追加，不覆盖历史。
- 失败也要记录。
- 未测试必须写 `Not Tested`。
- 部分通过必须写 `Partial`。
- 不得把计划写成已完成。
- 正式实验应记录 run_id、seed、主要配置和输出路径。
- 具体模板以 `memory.md` 为准。

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
