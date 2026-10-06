# 实验执行规范

## 目的

保证不同实验之间能够公平比较、结果能够复现，并使最终报告中的结论具有可信度。

---

## 一、实验最基本原则

一次实验只研究一个核心变量。

例如研究 Reward Shaping 时，应保持：

- algorithm 不变
- network 不变
- state 不变
- training budget 不变
- seed 集合不变

仅改变：

```text
reward_mode
```

---

## 二、正式实验与 Debug 实验区分

### Debug Run

用于：

- 检查代码
- 检查 loss
- 检查奖励
- 快速观察学习趋势

可以使用较短 episode。

Debug 数据不得用于最终报告结论。

### Official Run

用于最终报告。

必须：

- 固定 config
- 固定 seed
- 完整保存原始日志
- 保留模型
- 不得中途人工筛掉“不好看”的 seed

---

## 三、随机种子

最低要求：

```text
42
43
44
```

推荐：

```text
42
43
44
45
46
```

需要控制：

- Python random
- NumPy
- PyTorch
- Environment
- CUDA（如使用）

---

## 四、训练预算

同组算法比较时尽量统一：

- num_episodes
或
- environment_steps

优先使用 environment steps 作为更公平的预算指标。

---

## 五、评估协议

训练期间 reward 曲线不能代替正式评估。

正式 evaluate：

- epsilon = 0
- 或采用纯 greedy
- 独立 evaluation episodes
- 不更新网络
- 不写入 Replay Buffer

推荐每个模型评估：

```text
50 episodes
```

训练成本或时间有限时可降为：

```text
20 episodes
```

但所有算法必须一致。

---

## 六、核心指标

每个 run 至少记录：

```text
episode
episode_return
score
episode_length
epsilon
loss
global_step
```

最终汇总：

```text
mean_score
std_score
max_score
mean_return
mean_episode_length
```

---

## 七、Reward Shaping 特别要求

Reward Shaping 实验至少同时记录：

- total reward
- actual score
- episode length

原因：

一个策略可能通过“存活”或“靠近食物”获得大量 shaped reward，却没有真正提高吃食物能力。

如条件允许，将 reward 分项记录：

```text
food_reward
death_penalty
distance_reward
step_reward
```

---

## 八、算法对比要求

DQN / Double DQN / Dueling DQN 应尽量保持：

- 相同 hidden_dim
- 相近参数量
- 相同 optimizer
- 相同 learning rate
- 相同 gamma
- 相同 replay buffer
- 相同 batch size
- 相同 target update
- 相同 epsilon schedule
- 相同 seed
- 相同训练步数

Dueling DQN 因结构差异参数量不可能绝对相同，应在报告中说明。

---

## 九、实验命名

建议：

```text
{experiment}_{algorithm}_{state}_{reward}_seed{seed}_{timestamp}
```

例如：

```text
algorithm_dqn_state_v1_sparse_seed42_20261006_1800
```

---

## 十、输出文件

每个正式 run 建议产生：

```text
config.json
metrics.csv
summary.json
checkpoint.pt
```

可选：

```text
train.log
evaluation.json
```

不要只保存最终截图。

---

## 十一、绘图规则

正式汇报图：

- 不使用单次 seed 曲线代表算法结论。
- 推荐显示多 seed 均值。
- 可显示标准差或置信带。
- x 轴必须明确 Episode 或 Environment Step。
- y 轴必须明确指标。
- 图例统一算法命名。
- 不人为裁掉“难看”的训练区间。

---

## 十二、结论书写要求

错误示例：

```text
Double DQN 明显优于 DQN。
```

若只有一个 seed，不足以支持该结论。

更合理：

```text
在当前环境、训练预算和超参数下，Double DQN 在 3 个随机种子上的平均评估得分高于 DQN，并表现出更小的波动。
```

结论必须限定实验条件。

---

## 十三、异常记录

实验出现以下情况不能直接删除：

- NaN
- 长时间不学习
- 突然性能崩溃
- 某个 seed 表现异常
- 智能体绕圈
- 高 Return 低 Score

应记录：

- run_id
- 配置
- 表现
- 初步原因
- 是否重跑
- 重跑依据

---

## 十四、最终实验矩阵模板

| Experiment | Algorithm | State | Reward | Exploration | Seeds | Purpose |
|---|---|---|---|---|---|---|
| E0 | Random | V1 | Sparse | Random | 42-44 | Baseline |
| E1 | DQN | V1 | Sparse | Default | 42-44 | DQN baseline |
| E2 | DQN | V1/V2 | Sparse | Default | 42-44 | State |
| E3 | DQN | Best | Sparse/Shaped | Default | 42-44 | Reward |
| E4 | DQN | Best | Best | Varied | 42-44 | Exploration |
| E5 | DQN/DDQN/Dueling | Best | Best | Best | 42-44 | Algorithm |
| E6 | Best | Best | Best | Best | 42-46 | Final |

实际参数由项目运行结果确定，不要在实验前人为预设“最佳”结论。
