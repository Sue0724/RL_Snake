# Snake-RL

## 项目介绍

Snake-RL 是一个面向强化学习课程的小型研究型项目，目标是在自建贪吃蛇环境上实现并比较多种基于 DQN 的强化学习方法，同时研究状态表示、奖励设计与探索策略对智能体学习效果的影响。

项目最终应同时具备三类成果：

- 可运行成果：能够训练、评估并可视化展示强化学习智能体玩贪吃蛇。
- 实验成果：形成 Random / DQN / Double DQN / Dueling DQN 等方法的统一对比结果。
- 汇报成果：能够从环境建模、算法原理、奖励设计、实验设计、消融分析和最终 Demo 六个方面完整说明项目。

项目不以“单纯跑通代码”为完成标准，而以“可复现、可比较、可解释、可展示”为最终目标。

---

## 项目研究问题

本项目围绕以下问题展开：

1. 如何将贪吃蛇建模为一个标准强化学习问题？
2. 不同状态表示是否会影响 DQN 的学习效率与最终表现？
3. Reward Shaping 是否能够缓解奖励稀疏问题并加快收敛？
4. 不同探索策略及 epsilon 衰减方式如何影响训练过程？
5. Double DQN、Dueling DQN 相比标准 DQN 是否带来更稳定或更优的表现？
6. 在统一环境和评价指标下，哪一种组合能够获得最好的综合性能？

---

## 项目成员与主要分工

| 成员 | 主要方向 | 核心任务 | 报告主要内容 |
|---|---|---|---|
| A | 环境设计 | Snake 环境、动作空间、State V1（已冻结） | 环境建模 |
| B | DQN 基线 | DQN、Replay Buffer、Target Network | DQN 原理 + 基线实验 |
| C | 算法改进 | Double DQN、Dueling DQN | 改进算法 + 算法对比 |
| D | 实验设计与分析 | 状态设计（V2 及后续）、Reward Shaping、探索策略、综合实验 | 状态与奖励设计 + 消融实验 |

分工只用于确定主要责任人。所有模块最终必须进入同一工程、同一训练接口和同一评价体系，禁止形成四套彼此独立的项目。

---

## 项目目录

原有目录和文件名称保持不变，在此基础上补充工程公共模块和项目文档。

```text
Snake-RL/
│
├── env/
│   ├── snake_env.py
│   ├── renderer.py
│   └── random_agent.py
│
├── algorithms/
│   ├── dqn.py
│   ├── double_dqn.py
│   ├── dueling_dqn.py
│   ├── factory.py
│   └── networks.py
│
├── common/
│   ├── replay_buffer.py
│   ├── config.py
│   ├── utils.py
│   ├── checkpoint.py
│   └── metrics.py
│
├── experiments/
│   ├── state_experiment/
│   ├── reward_experiment/
│   ├── hyperparameter_experiment/
│   └── algorithm_experiment/
│
├── models/
│
├── results/
│   ├── logs/
│   ├── figures/
│   └── videos/
│
├── checkpoints/
│
├── docs/
│   ├── INTERFACE.md
│   ├── AI_DEVELOPMENT_RULES.md
│   ├── PROJECT_PLAN.md
│   ├── STAGE_CHECKLIST.md
│   ├── EXPERIMENT_PROTOCOL.md
│   ├── COLLABORATION_RULES.md
│   ├── HANDOVER.md
│   └── PROJECT_STATUS.md
│
├── tests/
│   ├── test_snake_env.py
│   ├── test_renderer.py
│   ├── test_random_agent.py
│   ├── test_play.py
│   ├── test_networks.py
│   ├── test_replay_buffer.py
│   ├── test_dqn.py
│   ├── test_agent_factory.py
│   └── test_checkpoint_loading.py
│
├── train.py
├── evaluate.py
├── play.py
├── smoke_test.py
├── requirements.txt
├── .gitignore
├── conftest.py
├── memory.md
├── codex.md
├── claude.md
├── QUICKSTART.md
└── README.md
```

说明：

- `env/snake_env.py`、`algorithms/dqn.py`、`algorithms/double_dqn.py`、`algorithms/dueling_dqn.py`、`experiments/state_experiment/`、`experiments/reward_experiment/`、`experiments/hyperparameter_experiment/`、`experiments/algorithm_experiment/`、`models/`、`results/`、`play.py` 均保持原名称。
- 新增文件只能用于补充统一训练、配置、评估、记录、可视化和工程规范，不得擅自重命名原有模块。

---

## 推荐技术栈

- Python 3.10+
- PyTorch
- NumPy
- Pygame
- Matplotlib
- Pandas
- 可选：Gymnasium 风格接口，但不要求强依赖 Gymnasium
- 可选：TensorBoard

推荐原则：

- 训练逻辑与渲染逻辑解耦。
- 默认训练时关闭实时 Pygame 渲染，避免显著拖慢训练。
- `play.py` 用于展示训练后模型，不承担主要训练职责。
- 所有实验必须通过统一配置运行，避免在不同脚本中手工修改超参数。

---

## 环境搭建

Python 3.10，conda 环境名固定为 `snake-rl`。每位成员在本地各建一份，不共享环境。

```bash
conda create -n snake-rl python=3.10 -y
conda activate snake-rl
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

torch 默认使用 CPU 版：本项目网络为小输入维度（State V1 为 11 维、V2 为 20 维）的小型 MLP，CPU 前向为微秒级，GPU 无收益。如需 GPU 版，参考 `requirements.txt` 顶部说明。

依赖清单见 `requirements.txt`。正式实验开始前应固定各依赖版本，保证不同成员结果可复现。

---

## 测试

```bash
python smoke_test.py   # Stage 0 自检：依赖、包结构、配置、目录
pytest                 # 代码测试，见 tests/
```

两者分工不同，不要合并：`smoke_test.py` 用于环境刚装完、还不知道依赖是否齐全时自检，本身不依赖 pytest；`tests/` 是环境就绪后的代码测试，由 pytest 驱动。

---

## 模型可视化演示

```bash
python3 play.py --agent model --checkpoint path/to/checkpoint.pt --seed 10000 --fps 20
```

将路径替换为训练输出目录中的 `checkpoint.pt`。模型模式从 checkpoint 恢复环境与网络配置，
以纯贪心策略跑一局，不训练、不保存模型。可指定 `--device`（默认 cpu）、`--seed` 和正整数 `--fps`；
不传 seed 时随机选择并打印，传入相同 seed 可复现。模型模式拒绝覆盖棋盘、状态、奖励和训练参数。
`Q` / `Esc`、关闭窗口或 `Ctrl+C` 可退出，结束时关闭窗口。
评估和演示共用单次 checkpoint 读取与恢复流程；预期加载失败显示模型路径及简洁原因，无 traceback。

随机与键盘模式仍可使用 `python3 play.py --agent random` / `python3 play.py --agent human`。

---

## DQN 基线训练

训练循环与基础日志已实际运行，三个种子各100k步训练完成。短程运行命令：

```bash
python3 train.py --num_episodes 100 --seed 42 --experiment debug_baseline
```

每次运行创建独立的 `results/logs/<run_id>/`，保存 `config.json`、
逐局 `metrics.csv`、训练 `summary.json` 和最新 `checkpoint.pt`。
默认无渲染、预热 1,000 步后开始更新。固定步数训练使用 `--total_steps 50000`，
此时覆盖局数预算。详细命令、日志解释及后续验收见 [QUICKSTART.md](QUICKSTART.md) 第六节。
独立评估入口已运行，DQN明显优于Random。评估模型及Random：

```bash
python3 evaluate.py --checkpoints results/logs/baseline_dqn_statev1_sparse_seed*/checkpoint.pt --compare_random
```

默认每个模型评估相同的 50 个环境种子，结果保存到 `results/evaluations/`。
详细说明见 QUICKSTART 第七节。Stage 2 的 13 项条件已满足并于 10-10 通过验收；收敛尚未确认。

---

## 强化学习问题定义

### 状态空间

第一版优先采用低维人工状态，保证 DQN 能够稳定学习。

建议至少包含：

- 前方是否存在碰撞危险
- 左侧是否存在碰撞危险
- 右侧是否存在碰撞危险
- 当前运动方向
- 食物相对蛇头的位置

后续状态实验可增加：

- 蛇头与食物的 Manhattan 距离
- 局部障碍信息
- 更细粒度方向编码
- 蛇身局部占用信息

不要在第一阶段直接上原始图像输入。

### 动作空间

推荐使用相对动作：

```text
0 = 直行
1 = 左转
2 = 右转
```

相比绝对的上下左右，相对动作能够避免非法反向动作，并减小策略学习难度。

### 奖励函数

基线奖励建议保持简单：

```text
吃到食物：+10
死亡：-10
普通移动：0
```

Reward Shaping 实验再引入：

- 靠近食物奖励
- 远离食物惩罚
- 每步微小惩罚
- 生存奖励
- 重复绕圈或长期未进食惩罚

奖励设计必须通过配置切换，不允许为每种奖励重新复制一套环境。

---

## 统一评价指标

所有算法使用统一指标。

核心指标：

- Episode Return
- Score / 吃到食物数量
- Episode Length
- 平均得分
- 最近 N 个 episode 的滑动平均得分
- 最高得分
- 成功存活步数
- 收敛速度
- 多随机种子下的均值与标准差

辅助指标：

- Loss
- Q Value
- epsilon
- 训练步数
- 训练时间

最终比较算法时，至少使用 3 个随机种子；时间允许时推荐 5 个随机种子。

---

## 阶段计划与完成标准

阶段编号不代表执行先后。10-10 调整后的实际执行顺序为 `2 → 3 → 6 →（4 · 5）→ 7 → 8`，权威说明见 [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) 的「执行顺序」一节。

### Stage 0：工程初始化与接口冻结

目标：

- 创建统一目录。
- 明确环境、Agent、训练和评估接口。
- 建立配置与日志规范。
- 建立随机种子控制。

完成标准：

- 项目可正常安装并启动：`python smoke_test.py` 全部通过。
- `snake_env.py` 的接口被书面确定。
- 所有成员理解输入输出约定。
- 不存在同功能的重复实现。

状态：`Pending`

存在问题：待项目初始化后填写。

---

### Stage 1：Snake 环境

目标：

- 实现贪吃蛇基础逻辑。
- 实现 `reset()`、`step(action)`、`render()`。
- 完成状态、动作、终止条件。
- 加入人工控制或随机 Agent 验证环境。

完成标准：

- 连续运行不少于 100 个 episode 无异常。
- 不允许蛇穿墙、食物生成在蛇身、非法反向等逻辑错误。
- 相同随机种子应尽可能复现相同初始状态。
- 训练模式可关闭渲染。
- Random Agent 能完整运行。

状态：`Passed`（10-07 由项目成员确认）

存在问题：无阻塞项。随机初始蛇头约 10% 落在最右列，属合法随机结果而非缺陷，详见 `docs/PROJECT_STATUS.md` 的 P2。

---

### Stage 2：DQN Baseline

目标：

- 实现 Q Network。
- 实现 Replay Buffer。
- 实现 Target Network。
- 实现 epsilon-greedy。
- 完成基本训练与模型保存。

完成标准：

- Loss 能正常反向传播。
- Replay Buffer 采样维度正确。
- Target Network 按配置更新。
- epsilon 按预设方式衰减。
- 训练结果明显优于 Random Agent。
- 能保存并重新加载模型。

状态：`Passed`（10-10 由项目成员确认）

存在问题：DQN 明显优于 Random（50 局均分 19.58～20.88 vs 0.04），但**收敛未确认**——该项不属本阶段验收项。

---

### Stage 3：统一训练与评估框架

目标：

- 完成 `train.py`。
- 完成 `evaluate.py`。
- 统一配置和日志格式。
- 训练与评估严格区分。

完成标准：

- 同一套命令可切换 DQN / Double DQN / Dueling DQN。
- 同一套命令可切换状态、奖励、探索参数。
- 实验结果自动保存到 `results/`。
- 模型自动保存到 `models/` 或 `checkpoints/`。
- 评估阶段默认关闭探索。

状态：`Passed`（10-10 由项目成员确认）

存在问题：渲染与退出验证使用 SDL dummy，新模型演示窗口的观感未经人工确认。

---

### Stage 4：状态设计实验

目标：

- 至少设计两种状态表示。
- 在相同算法、奖励和训练预算下比较。

完成标准：

- 除状态表示外，其余条件保持一致。
- 至少运行 3 个随机种子。
- 生成学习曲线和指标汇总。
- 能解释状态变化带来的性能差异。

状态：`Pending`

存在问题：待实验后填写。

---

### Stage 5：Reward Shaping 与探索策略

目标：

- 比较 Sparse Reward 与至少一种 Shaped Reward。
- 比较不同 epsilon 衰减策略或关键参数。

完成标准：

- 奖励方案由配置控制。
- 不允许同时修改多个变量后直接归因于 Reward Shaping。
- 形成 reward 实验曲线。
- 形成 exploration / hyperparameter 实验结果。
- 记录可能出现的“苟活”“绕圈”“不吃食物”等失败策略。

状态：`Pending`

存在问题：待实验后填写。

---

### Stage 6：Double DQN 与 Dueling DQN

目标：

- 基于 DQN 公共框架实现 Double DQN。
- 实现 Dueling DQN 网络。
- 不重复复制完整训练代码。

完成标准：

- Double DQN 的动作选择与目标值计算符合算法定义。
- Dueling DQN 能正确合并 Value 与 Advantage。
- 三种算法可通过配置切换。
- 单元测试或简单张量测试通过。
- 三种算法均可正常训练、保存和评估。

状态：`Pending`

存在问题：待算法实现后填写。

---

### Stage 7：统一对比与消融实验

目标：

形成最终实验矩阵。

至少包含：

- Random vs DQN
- State V1 vs State V2
- Sparse Reward vs Shaped Reward
- 不同 epsilon / hyperparameter
- DQN vs Double DQN vs Dueling DQN
- 最佳综合配置

完成标准：

- 所有正式对比使用统一训练预算。
- 所有曲线注明随机种子或均值方差。
- 保存原始 CSV/JSON 日志。
- 图表可以由脚本重新生成。
- 每个结论都能找到对应实验结果支持。

状态：`Pending`

存在问题：待综合实验后填写。

---

### Stage 8：最终 Demo 与课程汇报

目标：

- 完成可视化游戏 Demo。
- 输出最终图表。
- 整理报告和 PPT 所需素材。

完成标准：

- `play.py` 能加载最佳模型并展示。
- Demo 显示 Score、当前算法等必要信息。
- 至少准备训练前后对比。
- 至少准备 3 类核心图：
  1. 训练 Reward/Score 曲线
  2. 算法对比图
  3. 消融实验图
- 可以完整解释“为什么这样设计”和“结果说明什么”。

状态：`Pending`

存在问题：待最终汇报前填写。

---

## 每阶段执行规则

任何成员或 AI 编程助手在完成一个阶段后，都必须执行以下流程：

1. 运行当前阶段的最小测试。
2. 运行与已有模块的集成测试。
3. 更新 `docs/PROJECT_STATUS.md`。
4. 写明已完成内容。
5. 写明测试结果。
6. 写明仍存在的问题和潜在风险。
7. 明确给出“是否满足本阶段验收条件”的结论。
8. 未通过验收时不得主动进入下一阶段。
9. 通过验收后，由项目成员确认是否进入下一阶段。

AI 助手不得因为“代码看起来正确”就判定阶段完成，必须以实际运行结果为依据。

---

## 当前主要风险

### 1. Reward Shaping 导致错误策略

可能出现：

- 蛇通过绕圈获得较高奖励。
- 智能体倾向生存但不吃食物。
- 距离奖励过大，压过真正的吃食物奖励。

处理方式：

- 奖励项分开记录。
- 限制每步奖励量级。
- 必须同时观察 Score 和 Return。

### 2. 不公平算法对比

如果不同算法使用不同网络规模、训练 episode、随机种子或奖励函数，则最终结论缺乏可信度。

处理方式：

- 使用统一配置。
- 只改变当前实验研究变量。

### 3. 渲染拖慢训练

处理方式：

- 训练默认 `render=False`。
- Demo 和人工检查时再打开渲染。

### 4. 四人代码无法合并

处理方式：

- 环境接口与 Agent 接口在 Stage 0 冻结。
- 公共逻辑放入 `common/`。
- 禁止复制多份训练循环。

### 5. 单次实验结果偶然性较大

处理方式：

- 正式实验至少 3 个随机种子。
- 报告均值和标准差。
- 保留原始日志。

---

## 最终成果清单

课程提交前至少应具备：

- 完整项目代码
- README
- AI 协作规范
- 环境实现
- DQN
- Double DQN
- Dueling DQN
- Reward Shaping
- 状态实验
- 超参数 / 探索实验
- 统一训练脚本
- 统一评估脚本
- 模型权重
- 原始实验日志
- 实验图表
- 最终 Demo 视频或现场演示
- PPT / 报告所需结论

---

## 项目状态

项目实际操作历史请持续追加：

`memory.md`

`memory.md`：项目操作日志，记录每次与项目紧密相关的实际操作时间、操作内容、验证结果与影响；普通咨询不记录。

接口定义与工作交接请参考：

`docs/INTERFACE.md`（接口权威定义）、`docs/HANDOVER.md`（已完成工作的设计说明、后续分工与接续须知）

详细进度请维护：

`docs/PROJECT_STATUS.md`

阶段验收请维护：

`docs/STAGE_CHECKLIST.md`

实验执行规范请参考：

`docs/EXPERIMENT_PROTOCOL.md`

AI 统一开发规范请参考：

`docs/AI_DEVELOPMENT_RULES.md`

Codex 使用入口请参考：

`codex.md`

Claude Code 使用入口请参考：

`claude.md`
