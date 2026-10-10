# 项目执行计划

## 总体目标

通过自建贪吃蛇环境，实现并比较 DQN、Double DQN、Dueling DQN，并围绕状态设计、Reward Shaping、探索策略进行消融实验，最终形成可运行 Demo 和完整课程汇报材料。

---

## 执行顺序

阶段编号 0–8 沿用 Stage 0 的原始划分，**不代表执行先后**。10-10 调整后的实际执行顺序：

```text
Stage 0 → 1 → 2 → 3 → 6 →（4 状态 · 5 奖励/探索）→ 7 → 8
```

调整原因：Stage 4（状态）与 Stage 5（Reward）同由 D 执行，且 State V2 的 `food_distance` 与 Stage 5 的距离 shaping 编码的是同一个量，合并成一条流水线可避免奖励结论在换状态后不可迁移；Stage 6 提前，使 Stage 7 设计消融矩阵时三根轴（状态 / 奖励 / 算法）已齐备。阶段编号保持不变——重编号会波及全部文档与代码引用点，破坏面远大于收益。

**合并执行不放松单变量纪律**：Stage 4 组固定 `reward_mode=sparse` 只改 `state_mode`，Stage 5 组固定状态只改 `reward_mode`，两组分开跑、分开报（`docs/AI_DEVELOPMENT_RULES.md` §12 / §19）。

---

## Stage 0 工程初始化

### 工作内容

- 建立项目目录。
- 创建基础依赖。
- 设计 Environment API。
- 设计 Agent API。
- 设计 Config。
- 设计日志格式。
- 固定 seed 机制。
- 确认各成员开发边界。

### 输出

- 可运行项目骨架。
- README。
- AI 协作规范。
- PROJECT_STATUS。
- 统一接口定义。

### 验收

详见 `STAGE_CHECKLIST.md`。

---

## Stage 1 环境与状态

负责人：A

### 工作内容

- 贪吃蛇核心逻辑。
- 状态空间。
- 动作空间。
- 食物生成。
- 碰撞检测。
- episode 生命周期。
- Pygame 渲染。
- 无渲染训练模式。
- Random Agent 验证。

### 状态方案

优先完成 State V1。

State V2 等改进方案放入后续实验，不应阻塞基线开发。

### 关键原则

环境只负责：

```text
state + action
-> next_state + reward + terminated + truncated
```

不要把神经网络或算法代码写入环境。

---

## Stage 2 DQN Baseline

负责人：B

### 工作内容

- Replay Buffer。
- Q Network。
- Online Network。
- Target Network。
- epsilon-greedy。
- Bellman update。
- optimizer。
- checkpoint。
- 基础日志。

### 目标

先追求：

```text
正确 + 稳定 + 可复现
```

再追求高分。

---

## Stage 3 统一框架

负责人：团队共同确认，建议 B 主导

### 工作内容

统一：

- train.py
- evaluate.py
- config
- logging
- checkpoint
- metric
- seed

此阶段完成后，后续算法和实验不得再各自建立独立训练框架。

---

## Stage 4 状态实验

负责人：D（10-10 由 A 调整为 D；与 Stage 5、Stage 7 合并为同一条实验流水线）

### 研究变量

只改变状态表示。

### 建议实验

```text
State V1：
危险方向 + 当前方向 + 食物方向

State V2：
State V1 + 距离 / 局部空间信息
```

### 输出

- 原始日志
- 学习曲线
- 最终指标
- 状态设计分析

---

## Stage 5 Reward 与探索

负责人：D

### Reward 实验

建议至少：

```text
R0 Sparse Reward
R1 Distance-based Reward Shaping
R2 Step Penalty + Distance Shaping
```

不要一开始设计大量复杂奖励。

### 探索实验

可研究：

- epsilon_decay
- epsilon_end
- 线性 vs 指数衰减

### 风险

Reward Shaping 最容易产生“看似 Return 高、实际不会吃食物”的伪改进。

必须同时观察 Score。

---

## Stage 6 算法改进

负责人：C

### Double DQN

解决 DQN 中的 Q-value overestimation 问题。

### Dueling DQN

通过独立估计 state value 和 action advantage 改进 Q 网络结构。

### 输出

- 单独实现
- 与公共训练框架兼容
- 与 DQN 相同实验接口

---

## Stage 7 综合实验

负责人：D 主导，团队共同完成

### 最低实验矩阵

```text
E0 Random
E1 DQN baseline
E2 State comparison
E3 Reward comparison
E4 Exploration / hyperparameter comparison
E5 DQN vs Double DQN vs Dueling DQN
E6 Best configuration
```

### 正式实验要求

- 相同训练预算
- 固定 seed 集合
- 统一评价协议
- 完整保存 config
- 保存 CSV/JSON 原始数据

---

## Stage 8 Demo 与汇报

### Demo

推荐显示：

- Algorithm
- Episode / Score
- Current Reward
- Snake Length
- 可选：Current Action

### 图表

至少准备：

- Score / Episode
- Return / Episode
- 算法最终性能比较
- 状态或 reward 消融实验
- 多 seed 均值与波动范围

### 汇报故事线

```text
1. 问题背景
2. 强化学习建模
3. 环境与状态
4. DQN
5. 改进算法
6. Reward / Exploration
7. 实验
8. 消融分析
9. Demo
10. 结论
```

---

## 项目完成定义

以下条件全部满足才认为项目完成：

- 环境正确。
- 至少一个 DQN 能稳定学习。
- Double DQN 完成。
- Dueling DQN 完成。
- 至少一个状态实验完成。
- 至少一个 Reward Shaping 实验完成。
- 至少一个探索或超参数实验完成。
- 使用统一评价协议。
- 正式实验使用多个随机种子。
- 所有结论有数据支持。
- Demo 可运行。
- 图表可重新生成。
- 项目文档同步更新。
