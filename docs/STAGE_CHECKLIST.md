# 阶段验收清单

任何 Stage 完成后，必须逐项核对。

符号：

```text
[ ] 未完成
[x] 已完成
[!] 存在问题
[~] 待团队确认，不阻塞后续阶段
```

---

## Stage 0：工程初始化

- [x] 原有文件和目录名称保持不变
- [x] 新增公共目录合理
- [x] Python 环境可运行
- [x] requirements 或环境说明完成
- [x] Environment API 已确定
- [x] Agent API 已确定
- [x] 配置管理方案已确定
- [x] seed 控制已设计
- [x] 结果保存路径已确定
- [~] 所有成员理解接口

验收结论：`Pending`

问题：

- 「所有成员理解接口」标记为 `[~]`：接口文档已就绪（`docs/INTERFACE.md`、`QUICKSTART.md`），待各成员确认，不阻塞 Stage 1。
- Agent API 规格已冻结（`docs/INTERFACE.md` §12），B 实现时如需调整按 `AI_DEVELOPMENT_RULES.md` §20 流程变更。

---

## Stage 1：Snake 环境

- [x] reset 正常
- [x] step 正常
- [x] action 定义正确
- [x] 碰墙死亡正确
- [x] 撞自身死亡正确
- [x] 吃食物后增长正确
- [x] 食物不会出现在蛇身
- [x] terminated / truncated 正确
- [x] 状态维度固定
- [x] render 正常
- [x] 无 render 模式正常
- [x] Random Agent 可连续运行
- [x] 100 episode smoke test 无异常

验收结论：`Passed`（10-07 由项目成员确认，可进入 Stage 2）

问题：

- 13 项全部通过。`pytest` 54 项：`tests/test_snake_env.py` 41 项、`tests/test_renderer.py` 5 项、`tests/test_random_agent.py` 3 项、`tests/test_play.py` 5 项。
- 「render 正常」的自动验证覆盖 `rgb_array`（帧形状 / dtype / 随局面变化 / 分辨率跟随 `board_size`）与 `human`（能建窗、`draw()` 不抛异常）。`human` 模式的视觉效果已由项目成员实际游玩确认。
- 「Random Agent 可连续运行」由 `tests/test_random_agent.py` 3 项 + `test_random_agent_rollout_100_episodes`（100 局由 `RandomAgent` 驱动）覆盖。
- `README.md` Stage 1 完成标准中的其余四条同样满足：100 episode 无异常、无穿墙 / 食物落在蛇身 / 非法反向（相对动作空间天然不存在反向动作）、同种子可复现、训练模式可关闭渲染（`render_mode=None` 时不导入 pygame）。
- 验收期间修复两个问题：中文输入法吞键导致 `play.py --agent human` 键盘无响应（`stop_text_input()`）；`play.py` 固定使用 `Config.seed` 导致每次演示轨迹完全相同（改为不传 `--seed` 时随机取种子并打印）。两项均已记入 `memory.md`。
- 遗留（不阻塞，非缺陷）：随机初始蛇头可能落在边缘且朝向恒为右，约 3.3% 的开局第一步即撞墙。属合法随机结果，见 `memory.md` 与 `docs/PROJECT_STATUS.md` P2。

---

## Stage 2：DQN

- [x] Q Network forward 正常
- [x] Replay Buffer 正常
- [x] batch shape 正确
- [x] epsilon-greedy 正常
- [x] Bellman target 正确
- [x] loss 正常
- [x] backward 正常
- [x] optimizer step 正常
- [x] Target Network 正常更新
- [x] 模型可保存
- [x] 模型可加载
- [x] 训练不出现持续 NaN（3 seeds各100k步完成，记录loss有限）
- [x] 性能明显优于 Random（共同50局：DQN均分19.58～20.88，Random0.04）

验收结论：`Passed`（13/13，10-10 由项目成员确认）

问题：

- 10-10 项目成员在 Windows + conda `snake-rl` 环境复验：`pip check` 无冲突、`smoke_test.py` 6/6、全量 `pytest -q` **166 passed**；三个 100k 模型的独立评估以相同 50 局种子在本机重跑，平均分/标准差/最高分与 B 的 macOS 结果**逐位一致**；三个训练 run 各为 100,000 步、99,001 次更新、ε=0.05、status `completed`，记录 loss 无 NaN/Inf。100k 训练本身未重跑，只核产物完整性与跨平台可运行性（`train.py --total_steps 2000` 冒烟通过）。
- 10-10 第四步与第五步完成：Q 网络 11 项测试、回放池与集成 22 项测试通过；覆盖 11/20 维输入兼容性、梯度与单次 optimizer 更新、容量覆盖、状态副本、结束标记和环境到网络的数据流。State V2 环境本身仍未实现。
- 10-10 第六步与第七步完成：新增 DQN 29 项测试通过，验证动作选择、完成环境步骤后的衰减、普通/真终止/截断目标值、loss/梯度/optimizer、Target 同步及 checkpoint 加载后继续更新的一致性。无窗口全量回归 116 passed。
- 10-10 三个训练种子 42/43/44 均完成 100,000 环境步、99,001 次更新，训练状态 completed，记录的逐局 loss 有限；持续训练稳定性已有实际运行证据。
- 独立评估使用相同种子 10000～10049，每模型 50 局、纯贪心、不更新网络、不写回放池。DQN 平均分分别为 20.02 / 19.58 / 20.88，Random 为 0.04，性能验收项已有数据支持。
- 结果目录：`results/evaluations/evaluate_20261010_115603_654649_e7cff81b/`。100k 相比 50k 的三模型平均分从 18.49 提升到 20.16，但尚不能确认全部收敛（收敛不属本阶段验收项，记录备查）。

---

## Stage 3：统一框架

- [x] train.py 可运行（3 seeds 各 100k 步实际完成）
- [x] evaluate.py 可运行（3 模型与 Random 共同独立评估完成）
- [x] play.py 可加载模型（--agent model --checkpoint；配置恢复、纯贪心、渲染及退出已自动验证）
- [x] algorithm 可配置切换（公共入口按配置分派；DQN 可训练/加载，Random 仅评估/演示；未实现算法明确报错）
- [x] state_mode 可配置（Config / CLI / checkpoint 已接入；目前仅实现 v1）
- [x] reward_mode 可配置（Config / CLI / checkpoint 已接入；10-18 起支持 sparse / distance / distance_step）
- [x] seed 可配置（训练 seeds 42/43/44，独立评估 seeds 10000～10049）
- [x] 日志自动保存（各 run 已生成 config.json / metrics.csv / summary.json）
- [x] checkpoint 自动保存（周期及结束保存已有实现，训练模型已用于独立评估）
- [x] 评估默认关闭探索（training=False，纯贪心，不更新网络、不写回放池）
- [x] 正式结果不会被意外覆盖（run 目录含时间戳和 UUID，exist_ok=False；多次运行结果独立保留）

验收结论：`Passed`（11/11，10-10 由项目成员确认）

问题与剩余工作：

- play.py 已支持 checkpoint 模型演示；允许覆盖 seed / device / render_mode / fps，拒绝覆盖模型环境和训练参数。窗口关闭、Q / Esc、Ctrl+C 均可退出，环境正常释放。
- 公共 Agent 创建/加载与 algorithm 分派已完成：`algorithms/factory.py` 接入训练、评估及随机演示。后续算法实现属于 Stage 6，本阶段的勾选表示分派机制完成，不表示三种可训练算法已齐备。
- 10-18 D 已实现 V1/V2 状态与三种 reward_mode；配置接通不代表效果结论，状态与奖励各自控制变量实验。
- 配置来源及覆盖规则已写入 INTERFACE §14、README 与 QUICKSTART 第八节；训练→保存→评估→演示完整链已在测试中验证，相同 seed 下演示成绩与评估一致。
- 公共入口新增 14 项测试，无窗口全量回归 130 passed；短程训练→保存→加载→评估通过。既有 100k 模型复评的 200 条逐局记录及模型摘要与原结果一致，来源 checkpoint 哈希未改变；复评输出仅放临时目录。
- 模型演示新增17项测试，play专项22 passed；最终无窗口全量回归147 passed。现有seed42的100k模型用评估seed10000运行真实play CLI，score=22、steps=149，与独立评估记录一致，checkpoint哈希未改变。
- 公共加载错误与重复读取完善后新增19项测试：文件不存在、损坏、元数据/权重/optimizer/RNG错误的CLI提示一致；公共加载单次读取，原agent.load兼容、内存恢复零读取及下一次更新一致。最新无窗口全量166 passed；三100k模型与Random复评共200条记录和原摘要一致，来源模型哈希不变。
- 本次渲染和退出验证使用SDL dummy，未人工肉眼确认新模型演示窗口；该遗留项不阻塞验收。

---

## Stage 4：状态实验

负责人：D（10-10 由 A 调整为 D；与 Stage 5、Stage 7 合并为同一条实验流水线，在 Stage 6 之后执行）

- [x] 至少两个状态版本（V1 11 维 / V2 20 维）
- [x] 仅改变 state（奖励 sparse、DQN、探索和其他配置相同）
- [x] 相同训练预算（六模型各 100k 环境步）
- [x] 相同 seed 集合（42/43/44）
- [x] 至少 3 seeds
- [x] 原始日志保存（含六份训练/评估产物与 checkpoint）
- [x] 曲线生成（共享绘图脚本从原始日志生成）
- [x] 汇总指标生成（comparison.json / comparison.csv）
- [x] 有结果分析（D_WORK_SUMMARY 第 10 节）
- [x] 无明显不公平设置（两个状态在同一尾格修复环境重训；参数量差异已披露）

验收结论：技术项 10/10 满足，`Pending`（待团队确认，不自动标记阶段 Passed）。

问题：

- 全量 266 passed；600k 总训练步、300 局独立评估完成。正式结果 V1 19.17 ± 0.56、V2 22.19 ± 0.65。
- 20 维同时增加距离和局部环，且输入层多 1,152 参数；只评价整体方案，未证明统计显著性或收敛。

---

## Stage 5：Reward / Exploration

- [x] Sparse Reward 基准存在（原三 100k 模型复评指标一致、哈希不变）
- [x] 至少一种 Shaped Reward（distance / distance_step，边界与短程验证通过）
- [x] reward_mode 可配置（含两项系数，CLI / checkpoint 已接通）
- [x] 每项 reward 量级合理（本轮系数通过边界校验并记录分项；合理量级不等于性能改善）
- [x] Score 与 Return 同时统计（训练/评估均增加四个累计奖励分项）
- [x] 检查是否出现绕圈 / 苟活（450 局物理状态复放，本批无完整循环/超时）
- [x] 至少一种 exploration 对比（固定 V2 + sparse，三种 epsilon 衰减参数）
- [x] 至少 3 seeds（各模式 42/43/44，100k 步/模型、50 局评估）
- [x] 奖励与探索曲线完成（原始数据可重生成，探索另含实际 epsilon 曲线）
- [x] 奖励与探索分析完成（保留负结果，区分训练与贪心评估）

验收结论：`Pending`（10-18 十项技术条件满足，正式奖励、行为与探索分析完成，待团队验收确认）

问题：

- 本轮全量 291 passed，自检 6/6；奖励九模型 900k 训练步、450 局正式评估及逐局行为复放完成。
- sparse 22.19 ± 0.65、distance 19.89 ± 0.15、distance_step 21.31 ± 0.27；负结果保留。
- 探索另训练九模型 900k 步、评估 450 局；快/默认/慢均分 21.39 ± 0.96 / 22.19 ± 0.65 / 19.94 ± 0.34。
- 暂保留默认 0.9999，不以训练曲线先上升或最高分选优；Stage 5 不自动通过，Stage 7 已按用户指令进入 E5。

---

## Stage 6：算法改进

### Double DQN

- [x] Online Network 负责选动作
- [x] Target Network 负责评估
- [x] 与 DQN 共享公共模块
- [x] 训练正常

### Dueling DQN

- [x] Shared Feature 正常
- [x] Value Stream 正常
- [x] Advantage Stream 正常
- [x] 聚合公式正确
- [x] 输出维度正确
- [x] 训练正常

### 通用

- [x] 三算法可统一切换
- [x] 三算法可统一评估
- [x] 不存在重复训练系统

验收结论：`待团队确认`（技术项 13/13 已有测试与运行证据）

问题：

- 全量回归 `180 passed`；三算法训练/保存/加载/评估集成测试通过。
- 三算法各 3 seeds 的 20k 步调试评估完成：DQN 18.20、Double DQN 20.38、
  Dueling DQN 19.65，Random 0.10。该结果仅用于验收链路，不作为正式算法结论。
- 正式预算下的性能比较由 Stage 7 统一执行；当前不能宣称收敛或算法优劣。

---

## Stage 7：综合实验

- [x] Random baseline（E5 两评估集，各 50 局，0.04 / 0.12）
- [x] DQN baseline（当前环境 V1 与 V2 正式结果，不混用修复前成绩）
- [x] State experiment（D-02）
- [x] Reward experiment（D-03）
- [x] Hyperparameter / exploration experiment（D-04）
- [x] Algorithm experiment（D-05 / E5，九模型及新种子复核）
- [x] State x Reward 交互消融（D-06，完整 2x3 矩阵与逐 seed 差中差）
- [x] Best configuration（已测开发候选中固定DQN+V2+sparse+默认探索，E6五seed验证，不声称全局最优）
- [x] 统一训练预算（接受的正式模型均 100k 环境步，失败尝试单独登记）
- [x] 多 seed（前序42/43/44，E6扩展至42-46）
- [x] 保存原始数据（配置、CSV、JSON、checkpoint 与图表可重生成）
- [x] 生成最终图（前序比较/交互与E6四图可由原始数据重生成）
- [x] 所有结论可被数据支持（来源索引、逐seed表、负结果与结论限制完整）

验收结论：技术项13/13有证据，`Pending`（待团队正式确认，不自动标Passed）。

问题：

- E5、交互矩阵、E6见D_WORK_SUMMARY第13/14/15节和大纲；最终全量333 passed，自检6/6。
- 开发 DQN/Double/Dueling 均分 22.19/19.77/21.01，新复核 21.45/19.89/20.83；暂保留 DQN，不声称逐 seed 占优或更稳定。
- 两次保存故障保留，修复后完整九模型、900k 步及含 Random 的 1000 条评估审计通过。
- 交互消融新增六模型 600k 步/300 局，审计复用十二模型后形成完整 18 模型/900 局矩阵，未重复计数。
- V1 distance_step 小幅均值正差与 V2 负差并不构成稳定交互证据；保留全部 seed 与限制。
- E6新测试五seed均分20.76±2.64，Random0.12；保留16.54的较弱seed44，未按测试换入口，最终配置与全部来源已留档。
- 技术条件满足，正式验收仍待团队确认；Stage8实际报告/PPT与Demo未开展，不自动进入下一阶段。

---

## Stage 8：汇报

- [ ] Demo 可运行
- [ ] 最佳模型已保存
- [ ] 训练前 / 后效果可比较
- [ ] Reward 或 Score 曲线
- [ ] 算法比较图
- [ ] 消融实验图
- [ ] 项目架构图
- [ ] DQN 原理图
- [ ] 报告结论与实验数据一致
- [ ] 所有人清楚自己负责部分
- [ ] 能回答失败案例与局限性

验收结论：`Pending`

问题：

- 待填写
