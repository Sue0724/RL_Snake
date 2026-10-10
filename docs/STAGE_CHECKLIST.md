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

验收结论：`Pending`（13项条件满足，待成员确认）

问题：

- 10-10 第四步与第五步完成：Q 网络 11 项测试、回放池与集成 22 项测试通过；覆盖 11/20 维输入兼容性、梯度与单次 optimizer 更新、容量覆盖、状态副本、结束标记和环境到网络的数据流。State V2 环境本身仍未实现。
- 10-10 第六步与第七步完成：新增 DQN 29 项测试通过，验证动作选择、完成环境步骤后的衰减、普通/真终止/截断目标值、loss/梯度/optimizer、Target 同步及 checkpoint 加载后继续更新的一致性。无窗口全量回归 116 passed。
- 10-10 三个训练种子 42/43/44 均完成 100,000 环境步、99,001 次更新，训练状态 completed，记录的逐局 loss 有限；持续训练稳定性已有实际运行证据。
- 独立评估使用相同种子 10000～10049，每模型 50 局、纯贪心、不更新网络、不写回放池。DQN 平均分分别为 20.02 / 19.58 / 20.88，Random 为 0.04，性能验收项已有数据支持。
- 结果目录：`results/evaluations/evaluate_20261010_115603_654649_e7cff81b/`。100k 相比 50k 的三模型平均分从 18.49 提升到 20.16，但尚不能确认全部收敛；阶段验收仍待成员确认。

---

## Stage 3：统一框架

以下为已有功能进度核对及用户指定的公共入口统一工作，不代表 Stage 2 或 Stage 3 已通过正式验收。

- [x] train.py 可运行（3 seeds 各 100k 步实际完成）
- [x] evaluate.py 可运行（3 模型与 Random 共同独立评估完成）
- [x] play.py 可加载模型（--agent model --checkpoint；配置恢复、纯贪心、渲染及退出已自动验证）
- [x] algorithm 可配置切换（公共入口按配置分派；DQN 可训练/加载，Random 仅评估/演示；未实现算法明确报错）
- [x] state_mode 可配置（Config / CLI / checkpoint 已接入；目前仅实现 v1）
- [x] reward_mode 可配置（Config / CLI / checkpoint 已接入；目前仅实现 sparse）
- [x] seed 可配置（训练 seeds 42/43/44，独立评估 seeds 10000～10049）
- [x] 日志自动保存（各 run 已生成 config.json / metrics.csv / summary.json）
- [x] checkpoint 自动保存（周期及结束保存已有实现，训练模型已用于独立评估）
- [x] 评估默认关闭探索（training=False，纯贪心，不更新网络、不写回放池）
- [x] 正式结果不会被意外覆盖（run 目录含时间戳和 UUID，exist_ok=False；多次运行结果独立保留）

验收结论：`Pending`（11/11 项已有证据，待成员确认统一框架验收）

问题与剩余工作：

- play.py 已支持 checkpoint 模型演示；允许覆盖 seed / device / render_mode / fps，拒绝覆盖模型环境和训练参数。窗口关闭、Q / Esc、Ctrl+C 均可退出，环境正常释放。
- 公共 Agent 创建/加载与 algorithm 分派已完成：`algorithms/factory.py` 接入训练、评估及随机演示。后续算法实现属于 Stage 6，本阶段的勾选表示分派机制完成，不表示三种可训练算法已齐备。
- state_mode / reward_mode 勾选表示配置已接通，不表示已有多个可用版本；State V2 与 Shaped Reward 分别属于 Stage 4 / 5。
- 配置来源及覆盖规则已写入 INTERFACE §14、README 与 QUICKSTART 第八节；训练→保存→评估→演示完整链已在测试中验证，相同 seed 下演示成绩与评估一致。
- 公共入口新增 14 项测试，无窗口全量回归 130 passed；短程训练→保存→加载→评估通过。既有 100k 模型复评的 200 条逐局记录及模型摘要与原结果一致，来源 checkpoint 哈希未改变；复评输出仅放临时目录。
- 模型演示新增17项测试，play专项22 passed；最终无窗口全量回归147 passed。现有seed42的100k模型用评估seed10000运行真实play CLI，score=22、steps=149，与独立评估记录一致，checkpoint哈希未改变。
- 公共加载错误与重复读取完善后新增19项测试：文件不存在、损坏、元数据/权重/optimizer/RNG错误的CLI提示一致；公共加载单次读取，原agent.load兼容、内存恢复零读取及下一次更新一致。最新无窗口全量166 passed；三100k模型与Random复评共200条记录和原摘要一致，来源模型哈希不变。
- 本次渲染和退出验证使用SDL dummy，未人工肉眼确认新模型演示窗口；Stage 2 / Stage 3 正式验收仍由成员确认，本次未自动进入后续阶段。

---

## Stage 4：状态实验

- [ ] 至少两个状态版本
- [ ] 仅改变 state
- [ ] 相同训练预算
- [ ] 相同 seed 集合
- [ ] 至少 3 seeds
- [ ] 原始日志保存
- [ ] 曲线生成
- [ ] 汇总指标生成
- [ ] 有结果分析
- [ ] 无明显不公平设置

验收结论：`Pending`

问题：

- 待填写

---

## Stage 5：Reward / Exploration

- [ ] Sparse Reward 基准存在
- [ ] 至少一种 Shaped Reward
- [ ] reward_mode 可配置
- [ ] 每项 reward 量级合理
- [ ] Score 与 Return 同时统计
- [ ] 检查是否出现绕圈 / 苟活
- [ ] 至少一种 exploration 对比
- [ ] 至少 3 seeds
- [ ] 曲线完成
- [ ] 分析完成

验收结论：`Pending`

问题：

- 待填写

---

## Stage 6：算法改进

### Double DQN

- [ ] Online Network 负责选动作
- [ ] Target Network 负责评估
- [ ] 与 DQN 共享公共模块
- [ ] 训练正常

### Dueling DQN

- [ ] Shared Feature 正常
- [ ] Value Stream 正常
- [ ] Advantage Stream 正常
- [ ] 聚合公式正确
- [ ] 输出维度正确
- [ ] 训练正常

### 通用

- [ ] 三算法可统一切换
- [ ] 三算法可统一评估
- [ ] 不存在重复训练系统

验收结论：`Pending`

问题：

- 待填写

---

## Stage 7：综合实验

- [ ] Random baseline
- [ ] DQN baseline
- [ ] State experiment
- [ ] Reward experiment
- [ ] Hyperparameter / exploration experiment
- [ ] Algorithm experiment
- [ ] Best configuration
- [ ] 统一训练预算
- [ ] 多 seed
- [ ] 保存原始数据
- [ ] 生成最终图
- [ ] 所有结论可被数据支持

验收结论：`Pending`

问题：

- 待填写

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
