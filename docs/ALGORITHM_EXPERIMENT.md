# D-05：三算法正式综合对比（E5）

日期：2026-10-18。负责人 D；基于 C 已有算法与实验编排开展正式对比。

## 研究问题与范围

在此前状态、奖励和探索实验确定的开发条件下，比较 DQN、Double DQN、Dueling DQN。
只改变 algorithm，不修改算法核心实现，不把 C 的算法贡献算作 D 的新实现。
本轮为 Stage 7 的 E5，不等于整个综合阶段或最终配置 E6 完成。
用户明确要求继续下一项任务，按此指令启动；Stage 4/5/6 的团队验收不自动改为 Passed。

## 预先固定的协议

| 项目 | 设置 |
|---|---|
| 算法 | dqn、double_dqn、dueling_dqn |
| 状态 / 奖励 | V2（20 维）/ sparse |
| 环境 | 当前尾格修复版本，10x10，初始长度 3，每局最多 500 步 |
| 网络 | 隐藏层宽度 128，两层共享特征；Dueling 使用既有双流输出 |
| 其他参数 | lr=0.001、gamma=0.99、batch=64、buffer=100000、预热=1000 |
| 目标同步 | 每 1000 次成功更新 |
| 探索 | epsilon_start=1.0、end=0.05、decay=0.9999 |
| 训练 | 各 seeds 42/43/44，从头训练，各 100k 环境步，共九模型 900k 步 |
| 开发评估 | 每模型 50 局，环境 seeds 10000-10049，加入一次 Random 对照 |
| 新复核评估 | 相同模型每个 50 局，环境 seeds 20000-20049，加入一次 Random 对照 |
| 候选规则 | 开发集跨模型平均 Score 最高，平分按预定算法顺序；复核集不重新选优 |
| 执行 | CPU，每算法三进程并行，每进程 1 个 Torch 线程 |

两套评估均纯贪心，不更新网络、不写回放、不衰减训练 epsilon。
9 个模型 x 50 局 x 2 + Random 50 局 x 2 = 1000 条评估记录。
新环境种子不是新的训练 seed，两个评估集也不当作六个独立训练 seed。
全部九模型重新训练，不从 D-02/03/04 的同配置模型复制成绩。
参数量差异、训练时长及其局限在完成后按实际产物记录，不预设改进算法胜出。

## 复现命令

```powershell
.\.venv\Scripts\python.exe -m experiments.algorithm_experiment.run --state_mode v2 --seeds 42 43 44 --total_steps 100000 --num_episodes 50 --eval_seed 10000 --holdout_seed 20000 --official --experiment e5 --jobs 3 --torch_threads 1 --output_dir results/algorithm_experiments
```

旧命令仍默认 V1，新的 --state_mode v2 必须显式指定。
--official 校验最低 seed/算法/局数，不代表程序可自动判断训练预算足以收敛。
每次产生唯一实验根目录，algorithm_comparison.json 从 running 更新为 completed / failed / interrupted。
旧 API 的 evaluation_dir、algorithms 等字段保留，输出根目录新增时间戳与 UUID，不覆盖旧数据。
训练与评估入口仍是公共 train() / evaluate()，没有另建训练系统。

```powershell
.\.venv\Scripts\python.exe -m experiments.algorithm_experiment.plot --comparison results/algorithm_experiments/<run>/algorithm_comparison.json --bin_steps 5000
```

生成 training_curves.png、development_scores.png、holdout_scores.png。
曲线仅统计完整训练局，先算各 seed 分箱均值，再跨 seed 汇总；阴影为总体标准差。
柱图误差棒为三个模型均分的总体标准差（ddof=0），不是置信区间；Random 仅一个策略，不画跨训练 seed 变异。
训练曲线含探索，不能当成按时点独立贪心评估或收敛证明。

审计与表格导出：

```powershell
.\.venv\Scripts\python.exe -m experiments.algorithm_experiment.analyze --comparison results/algorithm_experiments/<run>/algorithm_comparison.json
```

每次生成独立 analysis/audit_<时间戳与UUID>/，含 summary.json 和 comparison.csv。
JSON 保存核验结果、每个训练 run 的记录数/参数量/时长/模型 SHA-256，以及两评估集的分组指标。
CSV 保存两组逐模型得分、逐局标准差、最高分、Return、局长和截断率。
记录的哈希是审计时模型指纹，不冒充评估前后的哈希对比；工具只读来源，不改模型与原始数据。

## 验证与记录要求

- 运行原算法编排测试与新增正式协议测试，包括串并行一致性、评估集隔离及失败记录。
- 审计九份完整配置、精确预算、loss、epsilon、奖励分项、checkpoint 参数量与 SHA-256。
- 核对两组全部评估记录、模型来源和关闭训练标志，重算逐 seed 与跨 seed 统计。
- 原始 config / CSV / summary / checkpoint 均保留，图表由脚本再生成。
- 结果、负结果、限制、报告段落与 PPT 提纲追加到 D_WORK_SUMMARY.md 第 13 节。
- 本轮E5不包含交互消融或E6；后续已分别在D-06、D-07完成，见个人汇总第14/15节。

## 当前执行记录

正式训练前，原有与新增算法编排测试共 19 passed（15.05s）。
新增审计异常测试后，专项 26 passed（32.32s），全量 315 passed（72.61s），8 条第三方弃用警告；自检 6/6。

首次正式运行 algorithm_v2_sparse_20261018_170549_139360_c7cc027b 失败：
Double DQN seed42 在 60,176 步保存 checkpoint.pt.tmp → checkpoint.pt 时出现 PermissionError / Windows 拒绝访问。
另两个 Double DQN 与三个 DQN 日志显示 completed，但本轮未完成整个网格、未统一评估，不能用于算法排名。
失败 manifest、原始日志和文件完整保留，不续接不含回放池的 checkpoint 冒充连续训练。
已申请沙箱外以同一参数、新 experiment 名 algorithm_v2_sparse_retry 从头重跑；权限/文件占用具体原因未被证实。
重跑依据是文件保存失败，不是观察到成绩后筛选 seed；正式结论只在完整且经审计的网格上形成。
获准后启动 algorithm_v2_sparse_retry_20261018_173744_167192_364cf11c，随后发生下述第二次保存失败。
该重跑也在 DQN seed42 的最终保存发生替换拒绝访问，experiment manifest 为 failed；
原模型 summary 留在 running/92322，而 CSV 已记录 100k 步，不能据此声称模型完整保存。
两次失败均保留，说明不能将错误简单归因沙箱；具体占用来源未证实。

针对公共保存入口增加最多 6 次 PermissionError 替换重试（总等待最多 6.2 秒），只保存一次临时快照，
不删除旧目标、不重新训练步骤、不修改 RNG，持续失败仍抛错；其他 IO 错误不重试。
同时修复最终保存失败未更新训练 summary 的问题，补记 failed 与实际计数。
新增四项测试验证临时失败恢复、持续失败保留旧快照、其他错误不重试及最终失败状态；4 passed（2.95s）。
修复后以短实验名 e5 重新运行同一完整网格，失败尝试不参与正式排名。

## 正式完成结果

接受的完整实验为 e5_20261018_174445_393629_8f54c9be，九模型均 completed，各 100k 步、99,001 更新、epsilon=0.05。
两套评估共 1000 条记录完成，包含每套 450 条模型记录与 50 条 Random 记录。

| 算法 | 开发均值 ± 跨 seed 标准差 | 新复核均值 ± 跨 seed 标准差 |
|---|---:|---:|
| DQN | 22.19 ± 0.65 | 21.45 ± 1.49 |
| Double DQN | 19.77 ± 0.74 | 19.89 ± 1.01 |
| Dueling DQN | 21.01 ± 1.01 | 20.83 ± 0.86 |
| Random（单策略，无跨训练 seed SD）| 0.04 | 0.12 |

按开发集规则暂保留 DQN；两组均分排名一致，但复核集差距缩小且非所有配对 seed 占优。
DQN 在复核集的均分标准差最大，不宣称同时更稳定；不做显著性、收敛或普遍最优判断。
状态/奖励/探索基于此前 DQN 开发实验顺序选择，本比较不是各算法独立调参后的性能上限。
参数量 DQN / Double 为 19,587，Dueling 为 19,716（+129，约 +0.66%）；训练时长不是受控速度基准。
交互消融已在 [D-06](STATE_REWARD_ABLATION.md) 完成，五seed最终验证已在 [D-07](FINAL_EXPERIMENT.md) 完成；已用评估集不能再作为未见调参测试集。

审计 14,348 条训练记录与 1000 条评估记录通过：配置、预算、更新次数、epsilon、loss、奖励分项、
模型来源、共同种子、六项逐模型统计及选优规则均核对完成。审计使用 max(预热量, batch_size) 核对更新起点。
最后全量 319 passed（48.51s），8 条第三方弃用警告，自检 6/6；三张正式图已目视检查。
失败两轮的 CSV 步数为 560,176 和 300,000，有效正式预算为 900,000；总执行 1,760,176 步，失败尝试不扩大训练 seed 数。

产物：[正式 manifest](../results/algorithm_experiments/e5_20261018_174445_393629_8f54c9be/algorithm_comparison.json)、
[审计 JSON](../results/algorithm_experiments/e5_20261018_174445_393629_8f54c9be/analysis/audit_20261018_175556_016801_2c7aa9f6/summary.json)、
[逐 seed CSV](../results/algorithm_experiments/e5_20261018_174445_393629_8f54c9be/analysis/audit_20261018_175556_016801_2c7aa9f6/comparison.csv)、
[三次尝试登记](../results/algorithm_experiments/e5_20261018_174445_393629_8f54c9be/analysis/audit_20261018_175556_016801_2c7aa9f6/attempts.json)。
完整分析、三张图与讲稿见 [个人工作汇总](D_WORK_SUMMARY.md) 第 13 节；[报告与 PPT 大纲](D_REPORT_PPT_OUTLINE.md) 已更新。
