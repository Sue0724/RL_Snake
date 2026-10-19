# D 的探索衰减实验

更新日期：2026-10-18。

## 任务与边界

D-03 奖励比较后，本轮 D-04 固定 V2 + DQN + sparse，只改变 epsilon_decay。
研究的是同一种 epsilon-greedy 策略的衰减速度，不是不同探索算法或线性/指数策略的比较。
不修改 Agent 的既有衰减语义，不在全局 Config 中改默认参数，也不预设哪个候选最佳。

## 预先固定的候选

每完成一个训练环境步：epsilon = max(epsilon_end, epsilon * epsilon_decay)。
第一个训练动作使用 epsilon_start；reset 不重置 epsilon，预热和终止步都计入衰减。
独立评估 training=False，始终纯贪心，不继续衰减训练 epsilon。

| 候选 | epsilon_decay | 起点 / 下限 | 到下限的已完成训练步数 |
|---|---:|---|---:|
| 快 | 0.9998 | 1.0 / 0.05 | 14,978 |
| 默认 | 0.9999 | 1.0 / 0.05 | 29,956 |
| 慢 | 0.99995 | 1.0 / 0.05 | 59,914 |

完成 t 步后的理论值为 max(0.05, decay ** t)，第 t 个动作则使用完成 t-1 步后的值。
记录在逐局 CSV 中的 epsilon 是该局最后一步衰减后的值，不能误画到动作发生之前。
三组在 100k 步时都会达到 0.05，但训练过程中探索经历不同；相同最终 epsilon 不代表相同训练过程。

## 控制变量

固定 10x10 棋盘、初始长度 3、每局最多 500 步、当前尾格修复环境。
固定状态 V2、稀疏奖励、两层 128 隐藏单元、学习率 0.001、gamma=0.99、batch_size=64。
buffer=100000、预热 1000、目标网络每 1000 次成功更新同步，其余参数也一致。
每个候选训练 seeds 42/43/44，各 100k 环境步；每模型评估 50 局，环境 seeds 10000-10049。
所有候选重新训练，不把之前保存的模型直接混入本次比较。
正式总计 9 模型、900k 训练步、450 局独立评估；候选与系数不按中途成绩调整。

## 运行方式

短程检查：

```powershell
.\.venv\Scripts\python.exe -m experiments.hyperparameter_experiment.run --epsilon_decays 0.9998 0.9999 0.99995 --seeds 42 --total_steps 2000 --eval_episodes 3 --experiment debug_exploration
```

正式比较：

```powershell
.\.venv\Scripts\python.exe -m experiments.hyperparameter_experiment.run --epsilon_decays 0.9998 0.9999 0.99995 --seeds 42 43 44 --total_steps 100000 --eval_episodes 50 --eval_seed 10000 --official --experiment exploration_v2_sparse --jobs 3 --torch_threads 1
```

脚本默认固定 V2 + DQN + sparse，拒绝其他状态/算法/奖励混入。
--jobs 3 使用三个独立 CPU 进程，每进程一个 Torch 线程；默认 --jobs 1。
使用复用的公共 train() / evaluate()，无额外训练循环，不恢复回放池续跑。
批量候选用 --epsilon_decays，不能用单个 --epsilon_decay 产生被忽略的参数。

## 输出与绘图

每次新建 results/exploration_experiments/<唯一run>/，保留配置、日志、模型与失败/中断状态。
comparison.json 记录候选、理论下限步数、实际最终 epsilon、更新次数及分组汇总。
comparison.csv 是逐 seed 评估摘要；logs 和 evaluations 中保留原始数据与模型。
目录内的模型/日志引用使用相对路径，可以随整个实验目录移动。

```powershell
.\.venv\Scripts\python.exe -m experiments.hyperparameter_experiment.plot --comparison results/exploration_experiments/<run>/comparison.json --bin_steps 5000
```

- training_curves.png：按已完成环境步分箱的训练 Score / Return，先算每个 seed 均值，再跨 seed 汇总。
- evaluation_scores.png：独立贪心评估得分，误差棒为三个模型均分的总体标准差（ddof=0），黑点是各模型均分。
- epsilon_schedules.png：理论曲线叠加首个训练 seed 的真实逐局 epsilon 点；正式审计检查全部模型的记录。

奖励定义相同，所以本轮 Return 具有相同单位；仍以独立评估 Score 为主要指标。
训练曲线包含各自探索率影响，不能直接把训练得分更快上升解释成更快收敛。

## 验证与后续分析

专项测试检查理论下限与 Agent 逐步衰减一致、评估不计步、输入验证、同组配置和串并行可复现性。
审核时逐局检查 epsilon 与 global_step 对应，并核对所有模型实际 100k 步/99,001 更新、有限 loss 和奖励记账。
各组评估种子、局数与关闭探索/更新/回放标志必须一致，不能只挑最好看的 seed。

最终报告三 seed 均值、波动、逐 seed 差异、局长与截断率，不用单局最高分或训练曲线替代主指标。
本轮只有三种预定系数、三个训练 seed、单一环境与预算；不声称普遍最优或未经检验的显著性。
当前使用开发评估种子，综合配置还需独立保留种子验证。
正式结果与 PPT 素材见 [D_WORK_SUMMARY.md](D_WORK_SUMMARY.md) 第 12 节。

## 2026-10-18 正式结果

九模型均完成 100k 步、99,001 更新，450 局独立评估完成。

| epsilon_decay | seed42 | seed43 | seed44 | 均值 ± 跨 seed 标准差 | 相对默认 |
|---|---:|---:|---:|---:|---:|
| 0.9998 | 22.58 | 21.36 | 20.22 | 21.39 ± 0.96 | -3.61% |
| 0.9999 | 22.96 | 22.22 | 21.38 | 22.19 ± 0.65 | 基线 |
| 0.99995 | 20.40 | 19.60 | 19.82 | 19.94 ± 0.34 | -10.13% |

默认候选在三个配对 seed 上均高于另两组，本轮暂保留 0.9999，不宣称普遍最优或显著性。
快组训练曲线更早上升，但最终贪心评估并未提高；训练表现不能直接解释为更快收敛。
慢组均分波动较小但得分较低；探索更久的因果解释还需更长预算等额外对照。
平均局长依次为 178.72 / 182.53 / 160.49，截断率均为 0%；最高分 41 / 35 / 39 不能代表平均表现。

审计全部 15,269 条训练记录：配置仅 epsilon_decay 和 seed 不同，预算完整，epsilon 对应已完成步数，
loss 有限、奖励分项一致。450 条评估记录种子对齐，探索/更新/回放关闭，均值与标准差重算一致。
无窗口全量回归 291 passed，自检 6/6；共享绘图调整后三条实验端到端测试通过，三张正式图已目视检查。

原始产物：[comparison.json](../results/exploration_experiments/exploration_v2_sparse_20261018_163701_745710_520966f1/comparison.json)、
[comparison.csv](../results/exploration_experiments/exploration_v2_sparse_20261018_163701_745710_520966f1/comparison.csv)。
三张正式图及 PPT 讲稿集中在个人工作汇总第 12.6 节。
