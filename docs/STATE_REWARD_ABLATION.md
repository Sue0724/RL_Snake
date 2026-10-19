# D-06：状态与奖励交互消融

日期：2026-10-18。负责人 D，属于 Stage 7，不包含最终配置 E6 或 Demo。

## 训练前固定的协议

研究同一种塑形奖励的得分变化，是否随状态 V1/V2 而不同。
组成完整 2 状态 x 3 奖励矩阵，算法固定 DQN；不同时改变探索或系数后归因某个因素。

| 状态 | sparse | distance | distance_step |
|---|---|---|---|
| V1 | 复用 D-02 正式模型 | 本轮新增 | 本轮新增 |
| V2 | 复用 D-03 正式模型 | 复用 D-03 正式模型 | 复用 D-03 正式模型 |

所有格子 seeds 42/43/44，每模型 100k 环境步、99,001 更新，50 局纯贪心评估，环境 seeds 10000-10049。
固定当前尾格修复环境、10x10 棋盘、初始长度 3、每局 500 步、隐藏宽度 128、lr=0.001、gamma=0.99。
batch=64、buffer=100000、预热=1000、目标每 1000 更新同步，epsilon=1.0→0.05、decay=0.9999。
距离系数 0.1、步惩罚 0.01，预定候选不依据中途结果调整。

新增 6 模型、600k 训练步、300 局评估；复用 12 模型、1200k 步对应的 600 局历史正式记录。
完整矩阵共 18 模型、1800k 训练步对应的 900 条评估，不是本轮新训练 18 模型或新评估 900 局。
V2 sparse 只取 D-03，不同时纳入 D-02/04/05 的同配置重跑，以免重复计数。

## 复用依据与边界

训练前已检查 12 份配置：除 state_mode / reward_mode / seed 外一致；两个来源 completed / official，
训练预算、训练/评估种子与 environment_revision 一致，不混用修复前模型或 D-01 短程调试。
训练后聚合工具还会检查每份配置、checkpoint、逐局日志、实际预算、epsilon、loss、奖励记账与评估摘要。
保留模型、原始日志和来源路径指纹，不改写旧实验，也不将复用结果冒充新增独立 seed。
近期训练入口只增加保存异常重试/状态记账，不改变采样、学习或 RNG；环境/状态/奖励定义未变。

## 分析指标预先定义

主指标为每模型 50 局平均 Score，然后跨三个训练 seed 汇总。
在同一状态内定义 shaping 效应：gain(state, reward) = Score(state, reward) - Score(state, sparse)。
交互对比定义为：

```text
interaction(reward) = gain(V2, reward) - gain(V1, reward)
```

先对每个配对训练 seed 计算差中差，再报告其均值与总体标准差（ddof=0）。
正值表示当前样本中 V2 的 shaping 相对效应更高；负值表示更低，不直接等于整体 V2 更差。
此标准差不是置信区间；只有三个训练 seed，不预设显著性或交互机制。
Return 定义随奖励变化，不能拿不同奖励的 Return 代替真实 Score 排名。
当前使用开发评估种子，不触碰 E5 已用新复核集，更不能把它再次说成未见测试集。
V2 是距离与局部占用的整体方案，还多 1152 参数；本轮不能将交互单独归因于距离特征冗余。

## 补齐 V1 塑形训练

```powershell
.\.venv\Scripts\python.exe -m experiments.reward_experiment.run --state_mode v1 --reward_modes distance distance_step --seeds 42 43 44 --total_steps 100000 --eval_episodes 50 --eval_seed 10000 --official --experiment ablate --jobs 3 --torch_threads 1 --output_dir results/ablation_experiments
```

复用公共 reward_experiment 编排及 train/evaluate，不修改核心训练、环境或算法。
输出唯一目录，失败也保留 manifest，使用已有保存重试，不覆盖旧实验。
原始来源、正式结果、交互图、测试与 PPT 讲稿已记录于本文件及个人工作汇总第 14 节。

## 聚合、审计与绘图

本轮补齐训练的目录为 ablate_20261018_182154_464727_64db71b9。

```powershell
.\.venv\Scripts\python.exe -m experiments.reward_experiment.ablation --state_comparison results/state_experiments/state_v1_v2_20261018_134610_974148_b458c91f/comparison.json --v2_reward_comparison results/reward_experiments/reward_v2_20261018_152348_243907_d0be64a1/comparison.json --v1_reward_comparison results/ablation_experiments/ablate_20261018_182154_464727_64db71b9/comparison.json
.\.venv\Scripts\python.exe -m experiments.reward_experiment.ablation_plot --comparison results/ablation_experiments/<factorial_run>/comparison.json --bin_steps 5000
```

每次聚合都新建 factorial_<时间戳与UUID>/，生成 comparison.json / comparison.csv，不改写来源。
JSON 记录三个来源、18 个模型路径、全部原始文件 SHA-256、六格统计和逐 seed 交互值。
摘要中的 source_unchanged_during_audit 只表示来源在本次审计期间未变，不冒充历史训练前后的模型哈希对比。
复用 evaluate.score_summary 重算评估统计，逐项核对记录；不同来源的预算、种子、环境版本或公共参数不一致即拒绝汇总。

三张图：state_reward_scores.png 为六格独立评估均分；interaction_effects.png 为各状态塑形增益与差中差；
training_scores.png 按状态分面展示三奖励训练 Score，不跨奖励比较 Return。
所有误差棒/阴影均为训练 seed 均值或配对差值的总体标准差，不是置信区间或显著性判断。

新增专项测试已 7 passed（8.05s），包含配对公式、完整矩阵与图表、来源不一致的拒绝。
实际 12 个复用模型先通过完整来源审计（62 个原始文件指纹）；新增训练完成后，整个矩阵再次核验通过。

## 2026-10-18 正式完成结果

新增六模型全部 completed，均 100k 步、99,001 更新、最终 epsilon=0.05，无需修改训练参数或删 seed。
全量 326 passed（53.15s），8 条第三方弃用警告；smoke_test.py 6/6。

| 状态 | sparse | distance | distance_step |
|---|---:|---:|---:|
| V1 | 19.17 ± 0.56 | 17.27 ± 1.50 | 19.61 ± 1.56 |
| V2 | 22.19 ± 0.65 | 19.89 ± 0.15 | 21.31 ± 0.27 |

均值和总体标准差来自三个模型各自的 50 局平均 Score，不是单局波动或置信区间。

| 奖励 | V1 相对 sparse 均值差 | V2 相对 sparse 均值差 | 交互均值 ± 配对差中差 SD |
|---|---:|---:|---:|
| distance | -1.90 | -2.30 | -0.40 ± 2.52 |
| distance_step | +0.44 | -0.87 | -1.31 ± 2.25 |

逐 seed（42/43/44）交互值：distance -3.26 / -0.82 / +2.88；distance_step -1.38 / -4.04 / +1.48。
两种方案都不是每个 seed 同一方向；不能凭均值负值宣称已证明稳定负交互或显著性。
V1 distance_step 的相对 sparse 差为 +0.06 / +3.14 / -1.88，均值 +2.29% 但异质性明显，未证明可靠改善。
纯 distance 在 V1 也使均分降低约 9.91%，因此不能把 V2 的负结果单独解释为其已包含距离信息。
当前六格中 V2 sparse 均分最高，暂保留已有候选，不因 V1 单格的小幅正均值重新挑选参数。
V2 相对 V1 的状态方案增益依奖励为 +3.01 / +2.61 / +1.70，但有容量差异和配对 seed 例外，不作机制归因。

本次审计共 28,721 条训练记录、900 条评估记录、93 个原始文件指纹；全部配置/预算/更新/epsilon/loss/
奖励记账/模型来源/共同种子和评估摘要一致，来源在审计期间未变，所有格子截断率均为 0。
参数量 V1 18,435、V2 19,587；本轮仍未分拆 V2 距离与局部环，不排除参数量/状态整体差异。
三图从原始日志生成并目视检查，未使用合成正式数据。

正式产物：[补齐训练 manifest](../results/ablation_experiments/ablate_20261018_182154_464727_64db71b9/comparison.json)、
[完整矩阵与审计 JSON](../results/ablation_experiments/factorial_20261018_182816_405632_23aee76b/comparison.json)、
[18 模型逐 seed CSV](../results/ablation_experiments/factorial_20261018_182816_405632_23aee76b/comparison.csv)。
三图与报告讲稿见 [个人汇总第 14 节](D_WORK_SUMMARY.md)，更新后的整体故事线见 [报告与 PPT 大纲](D_REPORT_PPT_OUTLINE.md)。
本项之后的E6五seed验证已在 [D-07](FINAL_EXPERIMENT.md) 完成；Stage7技术项满足，正式验收待团队，未自动进入Stage8。
