# D-07 / E6：最终配置五训练 seed 验证

日期：2026-10-18。本协议在新增训练和查看新测试成绩之前冻结。

## 固定方案与范围

候选来自 E5 与 D-06：DQN + V2 + sparse + 默认探索（1.0→0.05、decay=0.9999）。
10x10、初始长度3、每局500步、隐藏层128、lr=0.001、gamma=0.99、batch=64、buffer=100000、
预热1000、每1000成功更新同步目标；每模型100k环境步，其余配置不变。
这是既有开发候选的最终确认，不是全组合最优证明或三算法分别调参后的上限比较。

- 复用接受的 E5 中 DQN seeds42/43/44 三个模型，配置、预算、checkpoint 与指纹预检，不使用失败尝试。
- 新训练 seeds45/46 两模型，200k 新训练步；五模型对应总预算500k，不是本轮新训练五个模型。
- 开发集10000-10049：五模型与Random各50局，共300条记录；旧三模型和Random轨迹会重复既有开发评估，不当新增独立样本。
- 最终新测试集30000-30049：同一五模型与Random各50局，共300条记录；不再使用已看过的20000-20049作为未见集。
- 两套本轮执行共600条评估记录，训练seed总数为五，不因评估局数或复评而增加。
- 新训练CPU两进程、每进程1个Torch线程；纯贪心评估，不更新网络、不写回放。
- 测试前固定seed42作为后续模型入口，只是固定引用，不声称它最典型或普遍最好；报告保留全部五个seed，不按测试重选。
- 完成本轮后不再根据测试集调参；以后如调参，必须重新保留未见种子。

## 复现命令

```powershell
.\.venv\Scripts\python.exe -m experiments.algorithm_experiment.final --source_comparison results/algorithm_experiments/e5_20261018_174445_393629_8f54c9be/algorithm_comparison.json --jobs 2
```

新增 final.py 仅编排公共 train()/evaluate()，不改核心算法与默认 Config。
新建 results/final_experiments/e6_<时间戳与UUID>/，保留失败/中断状态、来源、复用/新增标识和原始产物。
algorithm_comparison.json 的算法只有 dqn，支持复用现有审计与绘图，不另建统计口径。
final_config.json 保存完整冻结配置、五模型路径及预先固定的seed42引用，不覆盖旧模型。

```powershell
.\.venv\Scripts\python.exe -m experiments.algorithm_experiment.analyze --comparison results/final_experiments/<run>/algorithm_comparison.json
.\.venv\Scripts\python.exe -m experiments.algorithm_experiment.final_plot --comparison results/final_experiments/<run>/algorithm_comparison.json --bin_steps 5000
```

审计全部五模型的预算、更新次数、epsilon、有限loss、奖励记账、配置与评估来源，核对开发/测试集种子与关闭训练标志。
三模型来源manifest、模型和训练原始文件在训练前后核对SHA-256；审计输出另保留当前全部五模型指纹。
主指标为五模型平均Score的均值±总体标准差（ddof=0），不是250个训练样本或置信区间。
报告最差/最好seed和全部配对成绩，不以最高单局分数、Return或测试最佳seed选模型。
本轮只推进Stage7，团队验收不自动通过，Demo与实际PPT属于后续Stage8。

## 执行记录

运行前专项7 passed（11.03s）；加入逐seed绘图后的最终全量333 passed（54.89s），8条第三方弃用警告，自检6/6。

## 2026-10-18 完成结果

run_id：e6_20261018_184033_503575_81385455。两个新增模型均completed，各100k步/99,001更新/epsilon=0.05。

| 训练seed | 开发均分 | 新测试均分 | 测试-开发 |
|---|---:|---:|---:|
| 42（复用、固定入口）| 22.96 | 22.78 | -0.18 |
| 43（复用）| 22.22 | 20.60 | -1.62 |
| 44（复用）| 21.38 | 16.54 | -4.84 |
| 45（新增）| 21.70 | 19.66 | -2.04 |
| 46（新增）| 24.72 | 24.20 | -0.52 |
| 五模型均值±总体SD | 22.60±1.19 | 20.76±2.64 | -1.84 |
| Random（单策略）| 0.04 | 0.12 | 不含跨训练seed SD |

最终新测试均分范围16.54-24.20，跨模型均分波动大于开发集；平均Return197.56、局长169.12、截断率0%。
开发集对应Return215.96、局长187.32、截断率0%；单局最高分39/43不作为选优依据。
新测试均分比开发样本低约8.14%，只是两组样本的描述，不足以将下降单独归因于过拟合或分布转移。
没有删除seed44或因seed46更高而替换预先固定入口，不宣称已收敛、所有seed稳定或新测试证明算法普遍优于其他算法。
完成后测试集已经使用，未来调参不能再次把它当作未见测试集。

审计五模型8,013条训练记录（新增3,263条）、600条评估记录通过；预算/配置/checkpoint、epsilon、loss、奖励记账、
共同种子、关闭训练标志、来源与六项摘要重算一致。13个复用来源文件在运行前后SHA-256一致。
四图已生成并目视检查：训练曲线、开发总体图、新测试总体图、五seed逐项图。

产物：[完整manifest](../results/final_experiments/e6_20261018_184033_503575_81385455/algorithm_comparison.json)、
[冻结配置和固定模型入口](../results/final_experiments/e6_20261018_184033_503575_81385455/final_config.json)、
[审计JSON](../results/final_experiments/e6_20261018_184033_503575_81385455/analysis/audit_20261018_184355_953893_304ba2f0/summary.json)、
[逐模型CSV](../results/final_experiments/e6_20261018_184033_503575_81385455/analysis/audit_20261018_184355_953893_304ba2f0/comparison.csv)。
图表与讲稿见 [个人工作汇总第15节](D_WORK_SUMMARY.md)，报告与PPT整体故事线见 [大纲](D_REPORT_PPT_OUTLINE.md)。
Stage7技术清单具备证据，正式验收仍待团队确认；未进入Stage8，实际报告/PPT制作和Demo待后续执行。
