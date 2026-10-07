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

- [ ] Q Network forward 正常
- [ ] Replay Buffer 正常
- [ ] batch shape 正确
- [ ] epsilon-greedy 正常
- [ ] Bellman target 正确
- [ ] loss 正常
- [ ] backward 正常
- [ ] optimizer step 正常
- [ ] Target Network 正常更新
- [ ] 模型可保存
- [ ] 模型可加载
- [ ] 训练不出现持续 NaN
- [ ] 性能明显优于 Random

验收结论：`Pending`

问题：

- 待填写

---

## Stage 3：统一框架

- [ ] train.py 可运行
- [ ] evaluate.py 可运行
- [ ] play.py 可加载模型
- [ ] algorithm 可配置切换
- [ ] state_mode 可配置
- [ ] reward_mode 可配置
- [ ] seed 可配置
- [ ] 日志自动保存
- [ ] checkpoint 自动保存
- [ ] 评估默认关闭探索
- [ ] 正式结果不会被意外覆盖

验收结论：`Pending`

问题：

- 待填写

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
