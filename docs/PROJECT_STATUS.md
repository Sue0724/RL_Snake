# 项目状态记录

## 当前状态

当前 Stage：`Stage 2 - DQN Baseline`（负责人 B，尚未开工）

总体状态：`Pending`

最后更新：`10-07`

Stage 1 已于 10-07 通过验收，成果已合入 `main`。Stage 2 未启动（负责人 B）。

A 的并行项——Stage 4 状态方案的纸面设计——**已完成**，写入 `docs/INTERFACE.md` §4（预定方案，待团队确认后冻结），不写代码，不构成跨阶段开发。

---

## 阶段总览

| Stage | 内容 | 状态 | 负责人 |
|---|---|---|---|
| 0 | 工程初始化与接口冻结 | In Progress | 全员 |
| 1 | Snake 环境与状态 | Passed | A |
| 2 | DQN Baseline | Pending | B |
| 3 | 统一训练与评估框架 | Pending | B / 全员 |
| 4 | 状态实验 | Pending | A |
| 5 | Reward 与探索实验 | Pending | D |
| 6 | Double DQN / Dueling DQN | Pending | C |
| 7 | 综合实验 | Pending | D / 全员 |
| 8 | Demo 与课程汇报 | Pending | 全员 |

状态只能使用：

```text
Pending
In Progress
Blocked
Passed
```

---

## 当前阶段目标

Stage 2（负责人 B，尚未开工）：

- Q Network、Online / Target Network。
- Replay Buffer。
- epsilon-greedy 与 Bellman update。
- optimizer 与 checkpoint。
- 基础日志。

进入 Stage 2 前 B 需先确定的项：

- `epsilon_decay` 的衰减语义与默认取值，方案见 `docs/AI_DEVELOPMENT_RULES.md` §12。

A 的并行项（仅文档，不写代码）：

- Stage 4 的状态方案设计（State V2 预定方案）**已完成**，写入 `docs/INTERFACE.md` §4，待团队确认后冻结。

---

## 已完成

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
- 已实现 `play.py`：`--agent random|human` 两种模式，`human` 支持 `W/A/S/D` 与方向键（相对转向）与 `Q` / `Esc` 退出；复用 `build_parser`，`-h` 中同时列出脚本自有参数与全部配置参数。
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

Stage 2（负责人 B，尚未开工）：

- [ ] 确定 `epsilon_decay` 的衰减语义与默认取值
- [ ] Q Network / Online + Target Network
- [ ] Replay Buffer
- [ ] epsilon-greedy 与 Bellman update
- [ ] checkpoint 存取
- [ ] 基础日志

Stage 4 前置（A，仅文档，已完成）：

- [x] State V2 方案设计，写入 `docs/INTERFACE.md` §4（预定方案，待团队确认后冻结）

---

## 当前存在的问题

### P0

无技术阻塞。

Stage 0 验收结论仍为 `Pending`，仅剩「所有成员理解接口」（`[~]`）待团队确认，不阻塞 Stage 1。

### P1

1. `epsilon_decay` 的衰减语义尚未冻结，阻塞 Stage 2 的 epsilon-greedy 实现。**决策方案与推荐已记入 `docs/AI_DEVELOPMENT_RULES.md` §12「待冻结：`epsilon_decay` 的衰减语义」**，含三种方案的换算表与推荐结论（每 step 衰减 + 默认值 `0.995` → `0.9999`）。B 在实现前必须选定并写回该节；D 的 Stage 5 探索实验依赖此语义。

2. Stage 2 尚未开工（负责人 B）。A 的 Stage 1 已完成并通过验收，当前无阻塞项，但项目整体处于等待状态。

### P2

1. 随机初始蛇头允许落在边缘，且初始朝向恒为向右，因此约 10% 的开局蛇头位于最右列，随机策略下约 3.3% 的 episode 在第一步即结束。属合法随机结果，非缺陷；对演示观感有轻微影响。若需改善应调整 `env/snake_env.py` 的 `_random_head` 取值域，会改动 Stage 1 已冻结的行为与既有测试，留待 Stage 8 前再议。

2. `human` 模式关闭输入法（`pygame.key.stop_text_input()`）的效果无法自动化测试——验证需要真人按键。回归风险由人工验证承担，`memory.md` 已记录。

---

## 最近一次测试

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

Stage 2（阻塞中，负责人 B）：

- B 需先定 `epsilon_decay` 的语义与默认取值，方案见 `docs/AI_DEVELOPMENT_RULES.md` §12（P1-1）
- B 实现前请读 `docs/INTERFACE.md` §12 的「实现须知」，其中说明签名参考实现与禁止硬编码 `state_dim` / `n_actions`
- B 从 `main` 开分支，不从其他人的 feature 分支开：`git checkout main && git pull && git checkout -b feature/dqn`（完整流程见 `docs/COLLABORATION_RULES.md`）

A 的并行项（仅文档，不写代码，不构成跨阶段开发）：

- ~~设计 State V2 方案~~ **已完成**：预定方案写入 `docs/INTERFACE.md` §4，Stage 4 依此实施
- 方案尚未冻结，其他成员如有异议按 `AI_DEVELOPMENT_RULES.md` §20 提出，Stage 4 开工前定稿

A 的其余工作边界（核对结论）：

- Stage 4 是 A 当前唯一可推进的阶段任务，但依赖 Stage 2（DQN）与 Stage 3（统一框架）先行，暂为 Blocked
- 另一项属 A 但排在 Stage 5：`env/snake_env.py` 的 `_compute_reward()` 中 shaping 分项（当前恒为 0，注释已标注 Stage 5 实现）
- Stage 3 / 7 / 8 A 为参与角色，Stage 6 不参与实现

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
