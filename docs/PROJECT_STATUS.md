# 项目状态记录

## 当前状态

当前 Stage：`Stage 7 - Unified Experiments`（E0-E6与交互消融技术项完成，待团队正式验收；未进入Stage8，Stage4/5/6验收状态不变）

总体状态：`In Progress`

最后更新：`10-18`

10-18 实际 PPT 交付：用户明确要求制作，已生成 [12页可编辑PPTX](../deliverables/Snake_RL_10min_editable.pptx) 与 [PDF预览](../deliverables/Snake_RL_10min_preview.pdf)。
包含12页中文演讲备注、3张原生数据图/嵌入工作簿、2张原生表格和可编辑环境/算法示意图；内容570秒+30秒预留。
当前未提供Artifact运行库，使用本机WPS PowerPoint兼容COM接口及OOXML制作，并实际重新打开导出12张1600x900预览、逐页目视检查。
包结构与几何检查均零问题，16组均值/SD及图表缓存/工作簿对齐正式数据，自动文字溢出候选为0；PDF为12页。
棋盘明确标注环境示意，没有附真实模型录像。课程报告、真实Demo及四人计时排练仍待；此前“实际PPT未生成”为历史记录，当前已交付PPT初版。
本次为用户指定的汇报材料制作，不自动确认Stage4–7验收或Stage8整体Passed，未重跑训练/评估/pytest，未提交或推送。

10-18 提示词定稿：用户将交给另一个智能体制作，已把 [ppt.md](../ppt.md) 改为可独立使用的中文 PPT 制作 prompt。
保留12页、570秒内容+30秒预留、四人分工和关键正式数据；移除长路径、开发/验收记录、重复讲稿与备用材料表。
要求可编辑PPTX、逐页备注、简洁图示和真实数据；无真实截图/录像时不冒充运行结果。本次仅交付提示词，不表示实际幻灯片已生成。

10-18 汇报时长调整：按用户要求将 [主讲大纲](../ppt.md) 压缩为 12 页、9 分 30 秒内容，加 30 秒换人/翻页预留，共约 10 分钟（答辩另计）。
A 1–3 页、B 4–5 页、C 6–7 页、D 8–12 页；正式状态/奖励/探索/算法和五 seed 结论保留，历史基线、20k 调试、消融及审计细节移入答辩备用。
原 29 页内容归档为 [完整素材版](PPT_FULL_OUTLINE.md)，修正归档后的相对链接；个人大纲入口同步。以下 29 页整合记录为压缩前历史，不代表当前主讲页数。
末页为真实运行素材预留 10 秒，包含在时长内，录像仍需准备；本次仅修改文档，不重新训练/测试，不改变验收状态。

10-18 汇报大纲整合：按用户要求统一 [全组 PPT 大纲](../ppt.md)，共 29 页，A/B/C/D 分别为 1–5 / 6–12 / 13–19 / 20–29 页。
保留 A/B/C 分工与历史实验数值，依据已有 V1 接口补齐缺失第 5 页；追加 D 的奖励、探索、综合消融与五 seed 最终验证。
统一每页七项内容并附素材来源，区分历史基线、短程调试与当前正式结果；29 页、203 个字段及 76 个本地链接检查通过。
本次仅文档整理，未重跑训练或测试；实际幻灯片、课程报告与 Demo 仍待制作，技术与团队验收状态不变。

10-18：经 D 明确要求，先固定 V1 + DQN 完成奖励实现与短程验证。新增 distance / distance_step、
可配置系数、训练及评估逐局奖励分项、奖励实验编排和可重生成绘图。
无窗口全量回归 **229 passed**，smoke 6/6；三个模式各 2,000 步、每模型 3 局调试评估完成。
已有三个 100k sparse 模型与 Random 共 200 局复评，六项指标与历史完全一致，来源模型哈希不变。
**正式奖励与行为分析在 D-03 完成，探索对比在 D-04 完成；Stage 5 技术项满足，正式验收仍待团队确认。** V2 与状态正式比较已完成。
本次属于用户指定的局部顺序调整，不代表 Stage 6 验收已确认，也不改变后续单变量实验纪律。

10-18 D-02：V1/V2 各三 seed、每模型 100k 步、50 局评估完成（600k 步、300 局）。
当前条件下，跨 seed 平均 Score 为 V1 **19.17 ± 0.56**、V2 **22.19 ± 0.65**（总体标准差，ddof=0），
均值约 +15.72%；三个配对 seed 均有提升。V2 波动略大，每 100 步食物数 12.15 对比 V1 12.22，
不声称更稳定、寻食效率更高或普遍最优。全量 **266 passed**、smoke 6/6。
移入旧蛇尾的 occupied 集合错误已修复，两种状态均在当前环境重新训练；不混用修复前历史成绩。

10-18 D-03：固定 V2 + DQN，三模式各三 seeds、100k 步/模型、50 局评估，九模型 completed。
sparse **22.19 ± 0.65**、distance **19.89 ± 0.15**、distance_step **21.31 ± 0.27**，
后两者较基线约 -10.37% / -3.94%；三配对 seed 都未超过 sparse，保留负结果。
distance_step 的 Return 和最高分更高但均分更低，不能据其选优。450 局复放未发现完整状态循环或超时，
主要结局为自撞；来源模型哈希未变。全量 **270 passed**，下一轮探索暂定 V2 + sparse。

10-18 D-04：固定 V2 + DQN + sparse，仅改变 epsilon_decay，九模型各 100k 步、450 局独立评估完成。
快 0.9998：**21.39 ± 0.96**；默认 0.9999：**22.19 ± 0.65**；慢 0.99995：**19.94 ± 0.34**（ddof=0）。
快/慢相对默认 -3.61% / -10.13%，三个配对 seed 均未超过默认，暂保留 0.9999。
快组训练曲线更早上升不代表最终策略更好或收敛更快；不声称普遍最优或显著性。
全量 **291 passed**、smoke 6/6；共享绘图调整后三条端到端测试通过。
探索指南见 [EXPLORATION_EXPERIMENT.md](EXPLORATION_EXPERIMENT.md)，Stage 7 仍未开展。

D 的个人成果与 PPT 素材集中于 [D_WORK_SUMMARY.md](D_WORK_SUMMARY.md)，
D-02 状态在第 10 节、D-03 奖励与失败案例在第 11 节、D-04 探索结果及讲稿在第 12 节。

10-18 D-05：用户明确要求继续，开展 Stage 7 E5。固定 V2 + sparse + 默认探索，三算法各 3 seeds、100k 步。
完整接受目录 e5_20261018_174445_393629_8f54c9be，九模型 completed；开发/新复核种子各 50 局/模型，含 Random 共 1000 条评估。
开发均分 DQN **22.19 ± 0.65**、Double **19.77 ± 0.74**、Dueling **21.01 ± 1.01**；
复核为 **21.45 ± 1.49 / 19.89 ± 1.01 / 20.83 ± 0.86**，Random 0.04 / 0.12。
按开发规则暂保留 DQN，但复核非逐 seed 占优，且 DQN 均分波动更大，不声称更稳定、显著性或普遍最优。
前序配置基于 DQN 选择，不是各算法独立调参上限比较；交互消融与最终五训练 seed 确认未完成。
两次 Windows 保存替换错误及失败产物均保留；补充有上限 PermissionError 重试与最终失败状态修复，最后全量 **319 passed（48.51s）**、smoke 6/6。
核验 14,348 条训练与 1000 条评估记录通过，参数量 DQN/Double 19,587、Dueling 19,716；三张图目视检查。
详见 [算法正式实验指南](ALGORITHM_EXPERIMENT.md)、个人汇总第 13 节与 [报告/PPT 大纲](D_REPORT_PPT_OUTLINE.md)。

10-18 D-06：新增 V1 distance / distance_step 共六模型、600k 步/300 局评估，复用 D-02/03 十二模型，形成 2x3 六格矩阵。
V1 sparse/distance/distance_step 均分 **19.17 / 17.27 / 19.61**，V2 为 **22.19 / 19.89 / 21.31**。
两种奖励的差中差均值 ± 配对 SD 分别 **-0.40 ± 2.52 / -1.31 ± 2.25**，逐 seed 方向不一致，未证实稳定交互机制。
V1 distance_step 均值 +0.44，但配对差 +0.06/+3.14/-1.88，不能宣称可靠提升；纯 distance 在 V1 也较差，不能单独归因 V2 距离特征冗余。
审计 18 模型、28,721 条训练与 900 条评估记录、93 个原始文件指纹通过，三图已目视检查；新增/复用计数分开保存。
全量 **326 passed（53.15s）**、自检 6/6；指南见 [状态与奖励消融](STATE_REWARD_ABLATION.md)，汇总第 14 节与九页 PPT 提纲已更新。
本轮不开展 E6，不自动通过 Stage 7 或进入 Stage 8。

10-18 D-07 / E6：冻结DQN+V2+sparse+默认探索，复用E5三模型，新训seeds45/46，各100k步，五模型总预算500k（新增200k）。
开发10000-10049与新最终测试30000-30049各300条评估（含Random），全部五seed数据保留，不按测试改参或改入口。
开发均分 **22.60±1.19**，新测试 **20.76±2.64**，Random0.04/0.12；新测试逐seed为22.78/20.60/16.54/19.66/24.20。
模型均分波动在新样本上更大，seed44低于开发集；不声称稳定、显著性、收敛或全局最优，固定入口仍为测试前选定seed42。
审计五模型8,013条训练/600条评估，13个复用来源指纹前后一致，200条重复开发记录复现一致；四图已目视检查。
最终全量 **333 passed（54.89s）**，自检6/6；见 [E6指南](FINAL_EXPERIMENT.md)、个人汇总第15节与十页PPT大纲。
Stage7技术清单13/13有证据，正式Passed须团队确认；不自动进入Stage8。

**Stage 1 / 2 / 3 均已通过验收。** Stage 1 于 10-07 确认；Stage 2 与 Stage 3 于 10-10 经项目成员确认。确认前由成员在 Windows + conda `snake-rl` 环境独立复验：`pip check` 无冲突、`smoke_test.py` 6/6、全量 `pytest -q` **166 passed**；三个 100k 模型的独立评估以相同 50 局种子在 Windows 上重跑，平均分 / 标准差 / 最高分与 B 的 macOS 结果**逐位一致**。

Stage 2 关键数据：三个种子各完成 100,000 步、99,001 次更新，ε 降至下限 0.05，逐局 loss 无 NaN/Inf；同一 50 局独立评估均分 20.02 / 19.58 / 20.88，Random 0.04。**收敛仍未确认**（seed43 从 50k 到 100k 下降 4.67%，逐局标准差约 7）——收敛不属 Stage 2 验收项，仅记录备查。

Stage 6 实现：`algorithms/double_dqn.py`、`algorithms/dueling_dqn.py` 和
`DuelingQNetwork` 已完成；Double DQN 由 Online Network 选下一动作、Target Network
评估，Dueling 按 `Q=V+A-mean(A)` 聚合。`factory.py` 已注册 `dqn`、`double_dqn`、
`dueling_dqn`，三种算法复用同一 `train.py` / `evaluate.py`，不存在重复训练循环。
全量测试 **180 passed**；三算法各 3 seeds 的 20k 步调试评估完成，均分为
DQN 18.20、Double DQN 20.38、Dueling DQN 19.65，Random 0.10。该短预算结果
只验证统一实验链路，不用于正式算法优劣结论；Stage 6 尚待项目成员确认。

**10-10 调整**：Stage 4（状态实验）负责人由 A 改为 D，与 Stage 5、Stage 7 合并为同一条实验流水线，在 **Stage 6 之后**执行。原因与单变量纪律见 `docs/PROJECT_PLAN.md` 的「执行顺序」一节。State V2 的纸面方案仍保留在 `docs/INTERFACE.md` §4（预定方案，改由 D 在 Stage 4 开工前定稿冻结）。

**流程记录（如实）**：Stage 2 / 3 的代码先经 PR #1–#3 合入 `main`，验收在合并之后补办，与 `docs/COLLABORATION_RULES.md`「未通过阶段验收的代码不进 `main`」不符。属既成事实，记录备查。

---

## 阶段总览

| Stage | 内容 | 状态 | 负责人 |
|---|---|---|---|
| 0 | 工程初始化与接口冻结 | In Progress | 全员 |
| 1 | Snake 环境与状态 | Passed | A |
| 2 | DQN Baseline | Passed | B |
| 3 | 统一训练与评估框架 | Passed | B / 全员 |
| 4 | 状态实验 | In Progress | D |
| 5 | Reward 与探索实验 | In Progress | D |
| 6 | Double DQN / Dueling DQN | In Progress | C |
| 7 | 综合实验 | In Progress | D / 全员 |
| 8 | Demo 与课程汇报 | Pending | 全员 |

状态只能使用：

```text
Pending
In Progress
Blocked
Passed
```

**阶段编号不代表执行先后。** 10-10 调整后的实际执行顺序：`2 → 3 → 6 →（4 · 5）→ 7 → 8`，权威说明见 `docs/PROJECT_PLAN.md` 的「执行顺序」一节。

---

## 当前阶段目标

Stage 7 本轮范围（10-18 用户明确要求继续）：

- E5 完成：同配置九模型、两评估集、Random 对照、数据审计、正式曲线与负结果分析。
- 原算法核心未修改；D 扩展 C 的实验编排与新增审计绘图，公共保存入口因真实故障补充有上限重试及失败记账。
- E0/E1/E2/E3/E4 已有同版本正式结果与来源索引，见报告/PPT 大纲中的矩阵；不混用旧环境模型成绩。
- D-06交互与E6五seed验证均完成，Stage7技术项满足，正式验收待团队确认，不进入Stage8。

Stage 4 本轮范围（10-18 用户要求继续下一项 D 工作）：

- 实现 V2 = V1 + 归一化当前食物距离 + 相对朝向八格占用环；四个方向与边界测试通过。
- 修正移入旧蛇尾时 occupied 集合漏掉新蛇头的错误；两个状态均在当前版本从头训练。
- 复用 train/evaluate 与共享绘图；记录模型参数量差异，控制 sparse 奖励和探索设置。
- 状态专项与实验回归已通过，全量 266 passed，smoke 6/6；正式 2 状态 x 3 seeds x 100k 比较、绘图与分析均完成。

Stage 5 本轮范围（10-18 用户指定先做奖励部分）：

- 三奖励模式通过 reward_mode 切换，默认系数 0.1 / 0.01；同一颗旧食物计算距离差。
- 补齐累计奖励分项，复用 train/evaluate 编排，按模式分组评估并使用同一评估 seed 列表。
- 新增 docs/REWARD_EXPERIMENT.md、奖励专项测试和 plot CLI；保留 sparse 基线与旧 checkpoint 兼容。
- D-03 正式奖励多 seed 对比与失败行为复放、D-04 正式探索比较均完成；State V2 已实现。

Stage 6 既有实现（负责人 C，实现与自检完成，待团队确认）：

- Double DQN：Online Network 选动作、Target Network 评估该动作，已实现。
- Dueling DQN：共享特征层 + Value / Advantage 双流 + 聚合公式，已实现。
- 与公共训练框架兼容，三种算法统一切换、统一评估，已通过专项、集成和全量回归。

Stage 6 的算法实现与原有调试在 State V1 + sparse 上完成。新增 shaping 属本次 D 的 Stage 5 工作，不回写或混入 Stage 6 的历史结果。

已确定的前置项（10-09 冻结，B 已据此实现）：

- `epsilon_decay` 按已完成的训练环境步衰减，默认值 `0.9999`，起点 `1.0`、下限 `0.05`；跨局延续、预热阶段计步、评估不衰减。详见 `docs/AI_DEVELOPMENT_RULES.md` §12。

---

## 已完成

- 10-10 **Stage 2 与 Stage 3 通过验收**（项目成员确认）。确认前由成员在 Windows + conda `snake-rl` 环境独立复验，不采信文档既有结论：`pip check` 无冲突；`smoke_test.py` 6/6、exit 0；无窗口全量 `pytest -q` **166 passed**（50.12s），与 B 报告的 166 一致；三个 100k 模型的独立评估以相同种子 10000～10049、每模型 50 局在本机重跑，平均分 / 标准差 / 最高分与 B 的 macOS 结果**逐位一致**（20.02/6.98/36、19.58/7.10/38、20.88/7.00/37、Random 0.04/0.20/1）；三个训练 run 的 `summary.json` 各为 100,000 步 / 99,001 更新 / ε=0.05 / status `completed`，配置除 seed 外完全相同，记录 loss 无 NaN/Inf。补充验证：`train.py --total_steps 2000` 在 Windows 上端到端跑通（exit 0）。100k 训练本身未重跑，只核产物完整性与跨平台可运行性。
- 10-10 按用户要求完善公共模型加载：新增 common/checkpoint.py 的 CheckpointError / read_checkpoint，统一文件、格式和恢复错误；play/evaluate CLI 显示来源路径及简洁提示，无 traceback。DQNAgent新增restore_checkpoint，原load(path)兼容；公共load_agent只读一次文件。新增19项测试，全量166 passed；三100k模型及Random的200条复评记录与原结果一致，来源模型哈希不变。

- 10-10 play.py 新增 --agent model / --checkpoint，复用公共加载入口，以纯贪心演示一局；模型参数来自 checkpoint，只允许覆盖演示 seed、设备、渲染及 FPS。自动演示支持 Q / Esc、窗口关闭和 Ctrl+C 退出。新增17项测试，最终无窗口全量回归147 passed；已有100k模型演示score=22、steps=149，与对应评估一致，模型哈希未改变。

- 10-10 按用户要求新增 algorithms/factory.py，统一 DQN/Random 创建、算法配置校验及 checkpoint 加载；训练、评估和随机演示接入公共创建入口。模型加载恢复保存配置，校验环境/网络维度，设备与渲染由调用方指定；现有 checkpoint 格式与评估字段保持兼容。
- 公共入口新增14项测试，无窗口全量回归130 passed；短程训练/保存/加载/评估通过。现有三seed的100k模型在相同50局复评中，200条逐局记录和各模型摘要与原结果一致，模型文件哈希未改变；输出仅使用临时目录。

- 10-10 从头完成三个seed的100k步训练与同种子独立评估；新旧配置和前50k训练记录一致，模型平均分18.49→20.16（+9.01%）。比较结果保存在新评估目录的comparison_50k_100k.json/.md；有平台迹象，但不足以确认均已收敛。

- 10-10 按用户要求补齐 `evaluate.py`：从 checkpoint 恢复 DQN，纯贪心、无网络更新、无回放池写入；支持多模型与同种子 Random 比较，输出独立评估 CSV/配置/摘要，保存来源模型路径，拒绝环境配置不一致的同组比较。本次评估入口 Not Tested，未产生新的评估成绩。

- 10-10 按用户要求新增 `train.py`、`common/metrics.py` 与 `common/utils.py`：接通无渲染 DQN 循环、预热采样更新、按步衰减和跨局重置；控制全局/环境/回放池种子。
- 逐局 CSV 记录基础指标、run 标识及完整局标志，预热 loss 留空；新建独立目录保存完整配置、训练摘要与最新模型。支持局数或精确环境步预算、周期快照及 Ctrl+C 保存。此次新增代码为 `Not Tested`，未执行训练、测试或独立评估。
- 10-10 完成第六步与第七步：新增 `algorithms/dqn.py`，实现 epsilon-greedy、Online/Target Network、Smooth L1 + Adam 更新，以及正确区分真终止与截断的 Bellman target；新增 `on_env_step` 在完成环境步骤后衰减，目标网络每 `target_update_interval` 次成功梯度更新硬同步。
- checkpoint 保存并恢复两套网络、optimizer、配置、epsilon、两种计数及动作采样 RNG 状态；保留加载方的设备，不包含环境与 Replay Buffer 状态。
- 新增 `tests/test_dqn.py` 29 项测试，含 160 步/129 次更新的环境集成检查；无窗口全量回归 116 项通过。基线的长期稳定性与得分表现尚未验证。
- 10-10 按用户要求补齐当前 Python 3.10 的项目依赖，`python3 smoke_test.py` 6/6 通过，`python3 -m pip check` 通过。
- 10-10 完成第四步 Q 网络：`algorithms/networks.py` 的 `QNetwork(state_dim, n_actions, hidden_dim)`，支持单状态和批量状态，输入/输出维度取自环境，两层 ReLU 隐藏层，输出原始 Q 值。
- 10-10 完成第五步 Replay Buffer：`common/replay_buffer.py` 的 `ReplayBuffer(capacity, seed)`，六项经历独立存储、状态副本、固定容量环形覆盖、均匀无放回采样，batch 为六个 NumPy 数组组成的 dict；接口及速查页同步。
- 新增 `tests/test_networks.py` 11 项与 `tests/test_replay_buffer.py` 22 项测试，包含环境 -> 回放池 -> Q 网络的集成检查；无窗口全量回归 87 项通过。
- 10-09 经用户确认冻结 epsilon 衰减规格，将 `Config.epsilon_decay` 默认值从 `0.995` 改为 `0.9999`；开发规范、接口定义与交接文档同步。对应动作选择与衰减逻辑已于 10-10 实现。

- 已确定项目主题：基于深度强化学习的贪吃蛇智能体设计与实验研究。
- 已确定核心算法方向：DQN、Double DQN、Dueling DQN。
- 已确定主要实验方向：状态、Reward Shaping、探索/超参数、算法对比。
- 已建立文档规范。
- 已建立 git 仓库并关联远程 `Sue0724/RL_Snake`，文档入库。
- 已建立代码包骨架：`env/`、`algorithms/`、`common/`、`experiments/`。
- 已冻结 Environment API、动作空间、State V1（11 维）、`info` 字段、seed 控制与默认参数，见 `docs/INTERFACE.md`。
- 已建立依赖环境：conda 环境 `snake-rl`（Python 3.10）+ `requirements.txt`，`README.md` 补充「环境搭建」一节，并新增 `.gitignore`。
- 已统一接口口径：`docs/AI_DEVELOPMENT_RULES.md` §9/§16/§17、`docs/PROJECT_PLAN.md`、`docs/STAGE_CHECKLIST.md` 中残留的 4 元组与 `done` 全部改为 5 元组与 `terminated / truncated`，全仓库已无残留。
- 已确定实验输出路径：`docs/INTERFACE.md` 新增第 11 节，固化 `results/` 目录、run 命名、产出文件与指标列。
- 已确定配置管理方案并实现 `common/config.py`：`@dataclass Config`（20 个字段）+ `parse_args()` 自动生成命令行参数；存档用 `dataclasses.asdict()` 写入 `config.json`，不引入 YAML。
- 已冻结 Agent API：`docs/INTERFACE.md` 新增第 12 节，定义构造参数、四个方法签名、batch 结构、Bellman target 与责任边界。
- 已新增根目录 `QUICKSTART.md`：接口速查页，供各成员快速对齐。
- 已新增根目录 `smoke_test.py`：Stage 0 自检脚本，检查第三方依赖、包结构、配置系统与项目目录。`README.md` 的 Stage 0 完成标准「项目可正常安装并启动」判定为该脚本全部通过。
- 已补齐 `docs/INTERFACE.md` 实现前的 4 处缺口：`close()` 与生命周期硬失败、碰撞判定（蛇尾例外）、非法 `state_mode` / `reward_mode` 行为、`initial_head` 参数与初始蛇位置规则。
- 已引入 pytest：`requirements.txt` 增加 `pytest>=7.0`，新增根目录 `conftest.py` 与 `tests/`，`README.md` 增加「测试」一节说明它与 `smoke_test.py` 的分工。
- 已实现 `env/snake_env.py`：`reset` / `step` / `render` / `close`，State V1（11 维）、相对动作、5 元组返回值、奖励分项、随机种子与蛇尾例外判定。
- 已实现 `env/renderer.py`：pygame 渲染，被 `snake_env` 惰性导入（`render_mode=None` 时完全不加载 pygame）；`rgb_array` 用离屏 `Surface` 不建窗口，`human` 建窗口并在标题栏显示 score。
- 已实现 `env/random_agent.py`：`select_action(state, training=True)` 签名对齐 `docs/INTERFACE.md` §12，可被 `train.py` / `evaluate.py` 直接替换为 DQN 而不改调用代码。
- 已实现 `play.py`：`--agent random|human|model` 三种模式；模型模式从 checkpoint 恢复配置并纯贪心演示，`human` 支持 `W/A/S/D` 与方向键（相对转向）与 `Q` / `Esc` 退出；复用 `build_parser`，`-h` 中同时列出脚本自有参数与全部配置参数。
- `common/config.py` 拆出 `build_parser()` / `config_from_args()`：入口脚本可先构造自己的 `ArgumentParser` 再交给 `build_parser` 追加配置字段，原 `parse_args()` 保留为薄封装。
- 已实现 `tests/test_renderer.py`（5 项）、`tests/test_random_agent.py`（3 项）、`tests/test_play.py`（5 项）；`tests/test_snake_env.py` 41 项，共 54 项通过。
- 已修复中文输入法吞键导致 `play.py --agent human` 键盘无响应：`env/renderer.py` 建窗后调用 `pygame.key.stop_text_input()`，经行为 A/B 确认。
- 已修复 `play.py --agent random` 每次演示轨迹完全相同：新增 `_pick_seed()`，不传 `--seed` 时随机取种子并打印复现命令；该行为只作用于 `play.py`，实验脚本仍严格受 `Config.seed` 控制。
- **Stage 1 验收 13 项全部通过，10-07 由项目成员确认，结论 `Passed`。**
- 已写出 **State V2 预定方案**（`docs/INTERFACE.md` §4）：V2 = V1 11 维 + `food_distance`（归一化 Manhattan 距离）+ `local_ring`（蛇头周围 8 格占用环），共 20 维；含追加理由、已知代价与实现要点。整节标注未冻结、待团队确认。
- 已确定 **Git 工作流**并写入 `docs/COLLABORATION_RULES.md`：`main` 为已完成阶段的集成线，各阶段一律从 `main` 开分支，阶段验收通过后合回 `main`，下一阶段再从更新后的 `main` 开分支。含开工 / 开发 / 合并三步命令与冲突高发文件提示。
- **Stage 1 成果已合入 `main`**（fast-forward，无合并提交、无冲突）：`main` 由 `1676df6`（仅包骨架）前进到 `fc04c26`（含 Stage 1 全部代码与文档，18 个提交），此后从 `main` 开分支即可拿到 `env/` 全部代码。
- 已做文档一致性全量核查并修订：`memory.md` 2 处自相矛盾、本文件当前状态段把已完成的 State V2 设计写成待办、状态维度被写死（`docs/INTERFACE.md` 与 `QUICKSTART.md` 各 2 处、`README.md` 1 处）、`QUICKSTART.md` 缺 State V2 线索、合并记录未写 commit hash、`docs/INTERFACE.md` 变更记录表行序非时间序。
- `docs/AI_DEVELOPMENT_RULES.md` §21 修订两处：新增「**追加时回头核对**」规则（同日追加前须回头改掉已被推翻的「发现的问题」与「后续影响」）；commit hash 禁令收窄为「普通提交不记 hash，**Git 合并 / 回滚 / tag 必须写明 hash**」——原禁令的理由「`git log` 已是权威记录」对 fast-forward 合并并不成立。
- 新增 **`docs/HANDOVER.md`**（工作交接与后续安排），供 B / C / D 阅读：A 已完成工作的设计动机（环境建模、State V1 的三段结构与两个盲区）、State V2 预定方案与待确认点、B / C / D / A 的后续分工与阶段依赖、接续工作须知、需要团队确认的三件事。该文档不复制规范正文，接口细节一律指向 `docs/INTERFACE.md`。`README.md` 目录树同步补上 `docs/INTERFACE.md`（此前缺失）与 `docs/HANDOVER.md`。

---

## 待完成

Stage 0（技术项全部完成，仅剩验收）：

- [x] 创建真实代码仓库结构
- [x] 创建依赖环境
- [x] 实现 config
- [x] 冻结 Environment API
- [x] 统一接口口径（4 元组 → 5 元组）
- [x] 冻结 Agent API
- [x] 完成 Stage 0 smoke test
- [x] 确定结果保存路径

Stage 1（全部完成）：

- [x] 补齐 `docs/INTERFACE.md` 实现前的 4 处缺口
- [x] 引入 pytest 与 `tests/`
- [x] 实现 `env/snake_env.py`
- [x] 实现 `env/renderer.py`
- [x] 实现 `env/random_agent.py`
- [x] 实现 `play.py`，可视化跑通一局
- [x] 100 episode 连续运行改用 Random Agent 驱动
- [x] `human` 模式视觉效果人工确认（`python play.py --agent human`）
- [x] 修复中文输入法吞键
- [x] 修复 `play.py` 演示种子固定
- [x] Stage 1 验收并由项目成员确认

Stage 2（全部完成，10-10 通过验收）：

- [x] 确定 `epsilon_decay` 的衰减语义与默认取值
- [x] Q Network 基础结构与前向计算
- [x] Replay Buffer 与 batch shape
- [x] Online + Target Network 的初始化和同步
- [x] epsilon-greedy 与 Bellman update
- [x] checkpoint 存取
- [x] 基础日志及实际训练输出
- [x] 基线训练数值稳定性及明显优于 Random

Stage 3（全部完成，10-10 通过验收）：

- [x] `train.py` / `evaluate.py` / `play.py --agent model`
- [x] `algorithms/factory.py` 统一创建与加载，算法按配置分派
- [x] `common/checkpoint.py` 统一读取与错误提示
- [x] config / seed / 日志 / checkpoint / 评估口径全部可配置并落盘
- [x] 正式结果不会被意外覆盖（run 目录含时间戳与 UUID）

Stage 6（负责人 C，实现完成，待团队确认）：

- [x] Double DQN
- [x] Dueling DQN
- [x] 与公共框架兼容，不存在重复训练系统
- [x] 三算法各 3 seeds 的 20k 步统一调试评估
- [ ] 团队验收确认

Stage 4 前置（A 设计，已完成；实施改由 D）：

- [x] State V2 方案设计，写入 `docs/INTERFACE.md` §4（预定方案，由 D 在 Stage 4 开工前定稿冻结）

---

## 当前存在的问题

### P0

无技术阻塞。

Stage 0 验收结论仍为 `Pending`，仅剩「所有成员理解接口」（`[~]`）待团队确认，不阻塞 Stage 1。

### P1

1. **收敛未确认**（不阻塞验收）。100k 下三模型平均分 20.16，但 seed43 从 50k 到 100k 下降 4.67%，逐局标准差约 7，模型间差距（0.86 / 1.30 分）小于噪声。Stage 2 验收项只要求「训练不出现持续 NaN」与「性能明显优于 Random」，两项均有数据支持；「收敛」从未被声称。后续如需，可增加独立评估局数与训练时点，**不必重跑已有的 100k 训练与评估**。

2. **渲染相关验证依赖人工**（不阻塞验收）。新模型演示窗口的观感未人工肉眼确认，自动验证用 SDL dummy；`human` 模式需真人按键。回归风险由人工验证承担。

### P2

1. 随机初始蛇头允许落在边缘，且初始朝向恒为向右。蛇头列取自 `{length-1, …, board_size-1}` 共 8 个取值，故 **12.5%**（`1/8`）的开局蛇头位于最右列；随机策略下 **约 10.8%** 的 episode 在第一步即结束，由三类撞墙构成：

   ```text
   最右列直行撞右墙    1/8 × 1/3 = 1/24 = 4.17%
   第 0 行左转朝上撞顶  1/10 × 1/3 = 1/30 = 3.33%
   第 9 行右转朝下撞底  1/10 × 1/3 = 1/30 = 3.33%
                                    合计 ≈ 10.83%
   ```

   20 万次实测：最右列占 12.48%，第一步即结束占 10.78%，与理论值吻合。属合法随机结果，非缺陷；对演示观感有轻微影响。若需改善应调整 `env/snake_env.py` 的 `_random_head` 取值域，会改动 Stage 1 已冻结的行为与既有测试，留待 Stage 8 前再议。

   *10-10 更正*：本条原记「约 10%」与「约 3.3%」均有误。3.3% 只计入了最右列直行一类，漏计第 0 行与第 9 行的转向撞墙。

2. `human` 模式关闭输入法（`pygame.key.stop_text_input()`）的效果无法自动化测试——验证需要真人按键。回归风险由人工验证承担，`memory.md` 已记录。

---

## 最近一次测试

10-18 D-07最终五seed验证：

- 新增final.py与final_plot.py，仅编排公共训练/评估及绘图；专项7 passed（11.03s），最终全量333 passed（54.89s），8条第三方弃用警告，自检6/6。
- run_id：e6_20261018_184033_503575_81385455，复用E5接受的DQN42/43/44，新训练45/46均completed、100k步/99001更新/epsilon=0.05。
- protocol预先锁定最终新测试30000-30049、固定引用seed42；评估不更新、不探索、不写回放，禁止按测试重选。
- 审计8,013条训练（新增3,263）、600条评估，配置/预算/checkpoint、epsilon/loss/奖励、来源与摘要均核对；13个复用文件哈希一致。
- E5旧三模型及Random的200条开发复评记录逐项复现，不作为更多独立样本；五seed总预算500k、只新增200k。
- results/final_experiments/e6_20261018_184033_503575_81385455/ 保留final_config.json、manifest、两模型原始日志/模型、两评估组与四图。
- analysis/audit_20261018_184355_953893_304ba2f0/ 保留审计及12行逐模型CSV；全部图已目视检查，截断率0。
- 技术验收条件满足不等于团队已确认；实际报告/PPT与Demo仍待制作，测试集已使用，未来再调参需新保留种子。

10-18 D-06 状态与奖励交互消融：

- 新增 ablation.py / ablation_plot.py、专项测试、STATE_REWARD_ABLATION.md，复用已有 reward 编排，不改核心逻辑。
- 训练 run_id：ablate_20261018_182154_464727_64db71b9，V1 distance / distance_step、seeds 42/43/44，六模型 completed，各 100k 步/99001 更新/epsilon=0.05。
- 新增 600k 步、300 局；复用 D-02 V1 sparse 与 D-03 V2 三奖励，共 12 模型、600 条评估。没有把其他同配置重跑重复计入。
- 聚合：results/ablation_experiments/factorial_20261018_182816_405632_23aee76b/，18 模型/900 条评估、comparison.json/.csv 与三张图。
- 核验 28,721 条训练记录、共同配置、checkpoint、精确预算、更新、epsilon、有限 loss、奖励分项、评估来源/摘要与 93 个指纹；来源在审计期间未变。
- 专项 7 passed（8.05s）、全量 326 passed（53.15s），8 条第三方弃用警告，自检 6/6；三图目视检查，所有格子截断率 0。
- 当前六格最高均分仍 V2 sparse；配对交互方向不一致，不作显著性或距离冗余机制归因，最终配置 E6 尚待。

10-18 D-05 正式算法实验与故障处理：

- 初期专项 19 passed；加审计后 26 passed，全量 315 passed；保存修复专项 4 passed，最后全量 319 passed（48.51s），8 条第三方弃用警告，自检 6/6。
- algorithm_v2_sparse_20261018_170549_139360_c7cc027b 与 algorithm_v2_sparse_retry_20261018_173744_167192_364cf11c 均失败，前者 Double seed42 在 60176 步保存失败，后者 DQN seed42 最终保存失败。
- 第二轮旧训练摘要停在 running/92322，但 CSV 达 100k，不能认为模型已完整保存；失败 manifest 与全部原始产物保留。
- 保存重试仅限 PermissionError 原子替换，最多六次、总等待 6.2 秒，不删除目标或重新走 RNG；持续/其他 IO 错误仍报错，最终保存失败会正确标 failed。
- 接受结果：results/algorithm_experiments/e5_20261018_174445_393629_8f54c9be/，九份配置仅 algorithm/seed 不同，各 100k 步/99001 更新/epsilon=0.05。
- analysis/audit_20261018_175556_016801_2c7aa9f6/ 保存审计、20 行逐模型比较 CSV 与三次尝试登记；三次共执行 1,760,176 步，只有最终 900k 参与正式比较。
- 全部 14,348 条训练记录 epsilon/累计步数/有限 loss/奖励记账核验通过；两套评估的模型来源、共同种子、关闭训练标志、六项摘要和选优重算通过。
- 模型指纹是审计时哈希，不伪称评估前后哈希对比；三张正式图已目视检查。新复核集已使用，未来调参需另留种子。

10-18 D-04 正式探索衰减实验：

- 新增 21 项测试，全量 291 passed（58.21s），8 条第三方弃用警告，自检 6/6；共享绘图调整后三项集成测试通过。
- 三种衰减参数各 seeds 42/43/44，从头训练 100k 步/模型、99,001 更新、最终 epsilon=0.05，共 900k 步。
- 核对九份配置仅 epsilon_decay / seed 不同；全部 15,269 条训练记录的 epsilon 与 global_step 一致，loss 有限，预算及奖励记账完整。
- 三组各 150 条独立评估记录，共 450 局，种子 10000-10049 对齐，探索/更新/回放关闭；均值及总体标准差重算一致。
- 产物：results/exploration_experiments/exploration_v2_sparse_20261018_163701_745710_520966f1/，九模型、原始日志、比较表与三张正式图保留，均已目视检查。
- 暂保留默认衰减，Stage 5 技术条件满足但不代替团队验收；Stage 7 未启动。

10-18 D-03 正式奖励与行为复放：

- 新增 4 项测试：串并行一致性、完整状态循环、撞墙诊断、原始逐局复放核验与拒绝篡改记录；全量 270 passed（50.64s，训练同时运行），8 条第三方弃用警告。
- 三种奖励各 seeds 42/43/44，全部 V2 + DQN，从头训练；每模型 100k 环境步、99,001 更新、epsilon=0.05，总计 900k 步。
- --jobs 3，每 CPU 进程 1 个 Torch 线程；实际配置仅 reward_mode 与 seed 不同。
- 每模型独立评估 50 局，种子 10000-10049，共 450 局；三个评估组均关闭探索/更新/回放写入。
- 已检查逐局预算之和、有限 loss、分项奖励与 Return；原始日志、九个模型、比较表和图均保存。
- 450 局原种子复放逐局匹配 Score/Return/局长/分项/结束标记，九个模型 SHA-256 前后未变。
- 每组 150 局，撞墙 20/24/20、自撞 130/126/130，超时与完整循环均 0；保留固定规则选出的六个失败案例及局面图。
- 正式目录：results/reward_experiments/reward_v2_20261018_152348_243907_d0be64a1/。
- 行为目录：上述目录下 behavior/analysis_20261018_153547_deb51a8a/；三张图均已目视检查。
- 当前系数 0.1 / 0.01 未带来平均得分改善，不声称所有 shaping 均无效；同一开发评估集、三 seed 和单预算是结论限制。

以下为此前状态任务与奖励调试记录。

10-18 D-02 状态实现与正式实验（与奖励验证相同的本机环境）：

- 专项 53 passed（包含奖励绘图回归）；无窗口全量 266 passed（19.99s），8 条第三方弃用警告；smoke 6/6。
- 新增 37 项测试：V2 维度/范围/四朝向八格、食物刷新、尾格占用不变量、三算法 V2 训练/加载/评估、状态实验及绘图。
- 六模型均 completed，各 100,000 环境步、99,001 更新、epsilon=0.05；配置仅 state_mode 与 seed 不同。
- 检查逐局预算之和、有限 loss、奖励分项与 Return 一致；各组 150 局评估，种子列表与关闭探索/更新/回放设置一致。
- 正式产物：results/state_experiments/state_v1_v2_20261018_134610_974148_b458c91f/。
- 已保存六个 checkpoint、完整训练/评估 CSV/JSON、比较表及两张图；图由原始数据生成，已目视检查。
- V1：18.98 / 18.60 / 19.94；V2：22.96 / 22.22 / 21.38。结果分析及限制见 D_WORK_SUMMARY 第 10 节。
- 模型参数量：18,435 对比 19,587；V2 是距离 + 局部环整体方案，不单独归因。

以下为本日较早的奖励任务验证记录，发生在尾格占用修复之前。

10-18 D 奖励实现验证（Windows，本地 `.venv` Python 3.12.7，CPU）：

- numpy 1.26.4 / torch 2.8.0+cu126 / pygame 2.6.1 / matplotlib 3.9.2 / pandas 2.2.2。
- smoke_test.py：6/6；无窗口 pytest -q：229 passed（21.82s），8 条第三方弃用警告。
- 新增 49 个测试：奖励边界、同轨迹动力学一致性、分项记账、旧 checkpoint、实验编排/中断与绘图。
- 三模式各 seed42、2,000 步 / 1,001 更新完成；每模型评估 seeds 10000-10002，仅调试，不推导性能结论。
- 调试产物：results/reward_experiments/debug_reward_20261018_133159_843981_21c52af2/。
- 曲线与评估图已由 plot CLI 从原始日志重生成并目视检查；图内明确标注 DEBUG / 1 training seed。
- 三个已有 100k sparse 模型及 Random 各 50 局复评，mean_score/std_score/max_score/mean_return/
  mean_episode_length/truncation_rate 与历史逐项一致；三个模型 SHA-256 未变。
- 兼容性产物：results/reward_compatibility/evaluate_20261018_133230_934981_b11c897a/。
- 初次环境检查缺 pygame（smoke 5/6）；旧 Anaconda MKL 与 Torch 在绘图时 OpenMP 冲突。
  已在项目 `.venv` 安装 pygame 与非 MKL 的 NumPy wheel 解决，未改全局依赖、未绕过运行库检查。
- git diff --check：通过。

以下为历史测试记录。

10-10 **Stage 6 算法实现与调试实验（Windows + 仓库内 `.venv` Python 3.10.4）**：

- `smoke_test.py`：6/6，exit 0。
- `pip check`：无依赖冲突。
- C 专项测试：`test_double_dqn.py`、`test_networks.py`、`test_agent_factory.py`、
  `test_algorithm_experiment.py` 共 39 passed。
- 无窗口全量回归：`pytest -q` **180 passed**（42.97s）。
- 统一调试实验：3 算法 × seeds 42/43/44 × 20,000 步，训练 9/9 completed；
  相同评估种子 10000～10019、每模型 20 局，评估状态 completed，wall clock 3.11s。
- 汇总路径：`results/evaluations/evaluate_20261010_222836_955475_b7e30d7e/`，
  包含 `algorithm_comparison.json`、逐局 `metrics.csv`、`summary.json`。

10-10 **验收复验（Windows）**：解释器 `C:\Users\panmingdong\.conda\envs\snake-rl\python.exe`（Python 3.10.21）；numpy 2.2.6 / torch 2.14.1+cpu / pygame 2.6.1 / matplotlib 3.10.9 / pandas 2.3.3 / pytest 9.1.1，与文档记录一致。

- `python -m pip check`：无冲突。
- `python smoke_test.py`：6/6 通过，exit 0。
- `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m pytest -q`：**166 passed**，50.12s。
- `python evaluate.py --checkpoints <3 个 100k 模型> --num_episodes 50 --eval_seed 10000 --compare_random --output_dir <%TEMP%>`：平均分 20.02 / 19.58 / 20.88，Random 0.04，标准差与最高分与 10-10 的 macOS 结果逐位一致；输出写到仓库外的临时目录，仓库保持 clean。
- `python train.py --total_steps 2000 --output_dir <%TEMP%>`：`completed`，1001 次更新，loss 有限，exit 0。
- 训练产物核对：三个 run 各 100,000 步 / 99,001 更新 / ε=0.05 / `completed`；逐局 loss 无 NaN/Inf。

以下为此前的 macOS 测试记录。

10-10 加载流程完善后：`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest -q`：166 passed（含19项新增测试）。专项84 passed；单次读取、内存恢复零读取、旧load接口兼容及恢复后的下一次更新一致。现有三100k模型和Random复评200条记录/摘要与原结果一致，checkpoint SHA-256不变；输出仅使用自动清理的临时目录。

10-10 模型演示实现后：`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest -q`：147 passed（play专项22项，新增17项）。训练→保存→独立评估→演示同seed成绩一致；现有seed42的100k模型用seed10000运行真实play CLI得到score=22、steps=149，与原评估一致，checkpoint哈希不变。渲染与退出自动验证使用SDL dummy，未人工确认新模型窗口观感。此前公共入口复评200条记录与原结果一致。

第八步训练与评估已实际运行：三seed各100k步、99,001次更新，逐局loss有限；同一50局评估均分20.02/19.58/20.88，Random0.04。详见results/evaluations/evaluate_20261010_115603_654649_e7cff81b/。以下为此前组件测试记录，本次全量回归结果见上段。

测试时间：`10-10`

测试内容：

- 本机解释器：`/Library/Frameworks/Python.framework/Versions/3.10/bin/python3`；项目依赖已安装到该解释器。numpy 2.2.6 / torch 2.14.1 / pygame 2.6.1 / matplotlib 3.10.9 / pandas 2.3.3 / pytest 9.1.1。
- `python3 -m pip check`：无依赖冲突。
- `python3 smoke_test.py`：6/6 通过，退出码 0。
- `python3 -m pytest tests/test_networks.py tests/test_replay_buffer.py -q`：33 passed，覆盖维度、原始 Q 值、梯度和单次 optimizer 更新、回放容量与采样、状态复制、两个结束标记及集成数据流。
- `python3 -m pytest tests/test_dqn.py -q`：29 passed；显式验证普通步目标 5.5、真终止目标 2.0、截断目标 7.5，及 checkpoint 继续执行相同 batch 更新的一致性。
- DQN 集成检查完成 160 个环境步骤、129 次更新，loss 均为有限值；使用小网络和缩短预热的测试配置，不作为正式实验结果。
- `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest -q`：116 passed。渲染相关回归使用无窗口模式，本次未重新人工游玩。
- `git diff --check`：通过。

结果：`Passed`（组件历史检查及本次训练/评估完成）。Stage 2 已满足 13/13 项条件并于 10-10 通过验收，Stage 3 同期通过（11/11）；Stage 1 历史验收见下节。

---

## Stage 1 最近一次验收测试

测试时间：`10-07`

测试内容：

```text
pytest（全量）
  tests/test_snake_env.py      41 passed
  tests/test_renderer.py        5 passed
  tests/test_random_agent.py    3 passed
  tests/test_play.py            5 passed
  54 passed in 4.38s

python play.py --agent random（端到端，真实入口，种子修复后）
  不传 --seed 连跑三次：种子 108758 / 106174 / 897872，步数 9 / 20 / 87
  --seed 7 连跑两次：均为 1 步（一致）
  --seed 0 连跑两次：均为 12 步（一致，边界正确）

python play.py --agent human（人工）
  项目成员实际游玩数次，渲染、按键、计分正常

python smoke_test.py（Stage 0 自检，config 改动后复跑）
  [PASS] 第三方依赖  numpy 2.2.6 / torch 2.14.1+cpu / pygame 2.6.1
                     / matplotlib 3.10.9 / pandas 2.3.3
  [PASS] 包结构      env / algorithms / common / experiments
  [PASS] 配置默认值   21 个字段，board_size=10 seed=42
  [PASS] 配置覆盖     覆盖与默认值隔离正常
  [PASS] 配置存档     config.json 可序列化（451 字节）
  [PASS] 项目目录     env / algorithms / common / experiments / docs
  6/6 通过
```

结果：

`Passed`（pytest 54 项全通过；`play.py` random 与 human 两种模式均实机验证；smoke test 6/6，exit=0）

---

## 下一步

Stage 6 收尾（负责人 C）：

- 项目成员复核当前分支的代码、`180 passed` 结果和调试实验产物。
- Stage 6 的团队验收仍待确认；D 后续按用户指令已完成 Stage 7 E5 正式 100k 算法比较，不代替 Stage 6 团队确认。

Stage 4 + Stage 5 + Stage 7（负责人 D，Stage 6 验收后执行）：

- 三个阶段**合并为一条流水线**，原因与单变量纪律见 `docs/PROJECT_PLAN.md` 的「执行顺序」一节
- 状态、奖励、探索、E5、交互消融与E6五seed最终验证均完成；下一项为团队验收和Stage8实际报告/PPT、Demo，未经确认不自动开展。
- **单变量纪律不因合并而放松**：Stage 4 组固定 `reward_mode=sparse` 只改 `state_mode`；Stage 5 组固定状态只改 `reward_mode`。两组分开跑、分开报
- `env/snake_env.py` 文件层面仍属 A 责任区：跨责任区修改需在提交信息里说明原因，A 事后 review

A（参与角色）：

- Stage 4 / 5 / 7 已转出，A 不再主导实验阶段
- 保留 `env/snake_env.py` 与 `renderer` 的文件维护责任，负责 D 改动的事后 review
- Stage 3 / 7 / 8 为参与角色；Stage 6 不参与实现

Stage 0 收尾项（不阻塞）：

- 所有成员理解接口（`[~]`，待团队确认）

**跨阶段说明**：Stage 0 验收结论仍为 `Pending`。依据 `AI_DEVELOPMENT_RULES.md` §6「除非用户明确要求跨阶段开发」，经用户同意，A 提前进入 Stage 1 实现环境代码；Stage 0 待团队确认后补办验收。

---

## 更新模板

每次完成工作后追加：

```text
### MM-DD - 简短标题

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
