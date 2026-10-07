# 项目状态记录

## 当前状态

当前 Stage：`Stage 1 - Snake 环境`（Stage 0 验收待团队补办，见「下一步」）

总体状态：`In Progress`

最后更新：`10-07`

---

## 阶段总览

| Stage | 内容 | 状态 | 负责人 |
|---|---|---|---|
| 0 | 工程初始化与接口冻结 | In Progress | 全员 |
| 1 | Snake 环境与状态 | In Progress | A |
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

Stage 0：

- 建立目录。
- 确定接口。
- 确定配置系统。
- 确定日志系统。
- 建立最小可运行骨架。
- 确保所有成员后续能够并行开发。

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
- 已实现 `tests/test_renderer.py`（5 项）、`tests/test_random_agent.py`（3 项）、`tests/test_play.py`（3 项）；`tests/test_snake_env.py` 41 项，共 52 项通过。
- Stage 1 验收 13 项全部通过，结论 `Passed`（待项目成员确认）。

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

Stage 1：

- [x] 补齐 `docs/INTERFACE.md` 实现前的 4 处缺口
- [x] 引入 pytest 与 `tests/`
- [x] 实现 `env/snake_env.py`
- [x] 实现 `env/renderer.py`
- [x] 实现 `env/random_agent.py`
- [x] 实现 `play.py`，可视化跑通一局
- [x] 100 episode 连续运行改用 Random Agent 驱动
- [x] Stage 1 验收

Stage 1 收尾项（不阻塞）：

- [ ] `human` 模式视觉效果人工确认：`python play.py --agent human`

---

## 当前存在的问题

### P0

无技术阻塞。

Stage 0 验收结论仍为 `Pending`，仅剩「所有成员理解接口」（`[~]`）待团队确认，不阻塞 Stage 1。

### P1

1. `epsilon_decay` 的衰减语义尚未冻结。**决策方案与推荐已记入 `docs/AI_DEVELOPMENT_RULES.md` §12「待冻结：`epsilon_decay` 的衰减语义」**，含三种方案的换算表与推荐结论（每 step 衰减 + 默认值 `0.995` → `0.9999`）。B 在 Stage 2 实现 epsilon-greedy 前必须选定并写回该节；D 的 Stage 5 探索实验依赖此语义。

2. `human` 模式的视觉效果尚未人工确认，见「待完成」中的收尾项。自动测试只覆盖到「能建窗、`draw()` 不抛异常」。

---

## 最近一次测试

测试时间：`10-07`

测试内容：

```text
pytest（全量）
  tests/test_snake_env.py      41 passed
  tests/test_renderer.py        5 passed
  tests/test_random_agent.py    3 passed
  tests/test_play.py            3 passed
  52 passed in 4.29s

python play.py --fps 400 --initial_head 5,5（端到端，真实入口）
  episode 结束（撞墙或撞蛇）：score=0  steps=12
  exit=0（窗口正常创建与关闭，无 pygame 启动横幅）

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

`Passed`（pytest 52 项全通过；`play.py` 真实入口跑通一局；smoke test 6/6，exit=0）

---

## 下一步

Stage 1 收尾（不阻塞 Stage 2）：

- 人工肉眼确认 `python play.py --agent human` 的渲染效果（需项目成员执行）
- 提交本批变更并推送 `feature/env`

进入 Stage 2 前需先定的两件事：

- 冻结 `epsilon_decay` 的语义（每步 / 每 episode）与默认取值，写入 `docs/AI_DEVELOPMENT_RULES.md` §12（见 P1-1）
- 项目成员确认 Stage 1 验收结论

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
