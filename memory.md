# 项目操作记录

## 10-06

操作类型：Docs / Git
结果：Passed

操作内容：
- 新增 `memory.md` 项目操作日志机制，并在统一 AI 开发规范中加入对应要求，README 同步说明。
- 本地 `Snake-RL/` 初始化 git 仓库并关联远程 `Sue0724/RL_Snake`，将现有 11 份项目文档作为首个 commit 推送至 `main`。
- 从 `docs/COLLABORATION_RULES.md` 的分支建议中删除 `dev`，保留 `main` + `feature/*`。
- 精简 `memory.md`：说明文字、字段要求与记录模板全部迁入 `docs/AI_DEVELOPMENT_RULES.md` §21，本文件只保留操作记录；日期格式改为 `MM-DD`，同日操作合并到同一条。
- 统一日期格式：`docs/PROJECT_STATUS.md` 更新模板改为 `MM-DD - 简短标题`。
- 建立代码包骨架：`env/`、`algorithms/`、`common/`、`experiments/`，各含一个 `__init__.py` 占位（git 不跟踪空目录）。
- 切换至 `feature/env` 分支，后续开发不再直接提交 `main`。
- 冻结环境接口：新增 `docs/INTERFACE.md`，定义 Gymnasium 5 元组返回值、动作语义、State V1（11 维）、`info` 分项字段、seed 控制与默认参数（10×10 / 初始长度 3 / 上限 500 步）。
- 更新 `docs/PROJECT_STATUS.md`：Stage 0 转为 In Progress，勾除已完成项。
- 建立依赖环境：conda 环境 `snake-rl`（Python 3.10.21，torch 2.14.1+cpu），新增 `requirements.txt` 与 `.gitignore`，`README.md` 补「环境搭建」一节。
- 更新 `docs/STAGE_CHECKLIST.md`：Stage 0 中「Python 环境可运行」「requirements 或环境说明完成」两项勾除。

涉及文件：
- `memory.md`、`README.md`
- `docs/AI_DEVELOPMENT_RULES.md`、`docs/COLLABORATION_RULES.md`、`docs/PROJECT_STATUS.md`、`docs/INTERFACE.md`、`docs/STAGE_CHECKLIST.md`
- `env/__init__.py`、`algorithms/__init__.py`、`common/__init__.py`、`experiments/__init__.py`
- `requirements.txt`、`.gitignore`

执行 / 验证：
- 全仓库检索 `dev`、`YYYY-MM-DD`，确认无残留引用。
- 推送后 `git status` 与远程一致，无 ahead / behind。
- 在 `snake-rl` 环境实跑：numpy 2.2.6 / torch 2.14.1+cpu / pygame 2.6.1 / matplotlib 3.10.9 / pandas 2.3.3 均可导入，numpy→torch 转换与 MLP 前向正常（实测参数量 1923）。

发现的问题：
- 直连 GitHub 不稳定，`git push` 多次失败。

后续影响：
- 后续代码开发应在 feature 分支进行，不直接改 main。
- 依赖环境为本机 conda 环境，各成员需按 `README.md`「环境搭建」自行创建。
- B/C/D 可依 `docs/INTERFACE.md` 并行开发；Stage 0 剩余项为 `common/config.py`、Agent API、结果保存路径、smoke test。

## 10-07

操作类型：Docs
结果：Passed

操作内容：
- 核对 Stage 0 验收清单，确认 5 项已完成、3 项待办（Agent API、配置管理方案、所有成员理解接口）。
- 统一接口口径：修正 `docs/AI_DEVELOPMENT_RULES.md` §9 的 4 元组与 `done`、§16 调试顺序、§17 环境测试要求，以及 `docs/PROJECT_PLAN.md`、`docs/STAGE_CHECKLIST.md` 中的同类残留，全部改为 5 元组与 `terminated / truncated`。
- `docs/INTERFACE.md` 新增第 11 节「实验输出约定」：固化 `results/` 目录、run 命名、产出文件与 `metrics.csv` / `summary.json` 字段。
- 更新 `docs/STAGE_CHECKLIST.md`：Stage 0 勾选 5 项，写明剩余 3 项。
- 更新 `docs/PROJECT_STATUS.md`：最后更新改 10-07，已完成 / 待完成 / P0 / 最近一次测试 / 下一步同步。
- 确定配置管理方案并实现 `common/config.py`：`@dataclass Config`（20 个字段）+ `parse_args()` 自动生成命令行参数，写入 `docs/AI_DEVELOPMENT_RULES.md` §12 与 `docs/INTERFACE.md` §10。
- 冻结 Agent API：`docs/INTERFACE.md` 新增第 12 节，定义构造参数、四个方法签名、batch 结构、Bellman target 与责任边界。
- 新增根目录 `QUICKSTART.md`：接口速查页（环境搭建、环境 API、State V1、配置、Agent、实验输出）。
- `docs/STAGE_CHECKLIST.md` 新增 `[~] 待团队确认，不阻塞后续阶段` 符号，「所有成员理解接口」标记为 `[~]`。
- 新增根目录 `smoke_test.py`：Stage 0 自检脚本，6 项检查（第三方依赖 / 包结构 / 配置默认值 / 配置覆盖 / 配置存档 / 项目目录），并据此判定 `README.md` Stage 0 完成标准「项目可正常安装并启动」。`README.md` 补齐目录树（`smoke_test.py`、`requirements.txt`、`.gitignore`、`QUICKSTART.md`）。
- 提交并推送 `1091cfd feat: add stage 0 smoke test` 至 `feature/env`。
- 按用户在 4 个待定项上的决定，补齐 `docs/INTERFACE.md` 4 处缺口：§1 增加 `close()` 与「reset 之前 / done 之后再 step 抛 `RuntimeError`」；§4 增加碰撞判定小节（蛇尾是唯一例外，`danger_*` 与 `step()` 共用同一判定）；§6 增加非法 `reward_mode` 抛 `NotImplementedError`；§8 增加 `initial_head` 参数与初始蛇位置规则；§10 key 数 4 → 5。
- 引入 pytest：`requirements.txt` 增加 `pytest>=7.0`，新增根目录 `conftest.py`（其所在目录被 pytest 加入 `sys.path`，使 `tests/` 可直接 `import env`）与 `tests/`，`README.md` 增加「测试」一节说明它与 `smoke_test.py` 的分工。
- `common/config.py` 增加 `initial_head: tuple[int, int] | None = None`（字段数 20 → 21），`_arg_type` 增加 tuple 分支与 `_parse_int_pair`，命令行写法 `--initial_head 4,6`。
- 实现 `env/snake_env.py`：`reset` / `step` / `render` / `close`、`state_dim` / `n_actions`；`body`（deque）+ `occupied`（set）双结构，只在 `_place_snake` 与 `_advance` 中同时改动；转向用旋转公式而非查表；`reward_mode` / `state_mode` 非法取值在 `__init__` 中硬失败。
- 实现 `tests/test_snake_env.py`：41 项，覆盖 `docs/STAGE_CHECKLIST.md` Stage 1 的 11 项，含「danger 位与实际 step 结果逐动作比对」的一致性测试。
- 实现 `env/renderer.py`：`human` / `rgb_array` 两种模式，被 `snake_env` 惰性导入，`render_mode=None` 时完全不加载 pygame；`rgb_array` 用离屏 `Surface` 不建窗口，`human` 在标题栏显示 score。`draw()` 末尾只调 `pygame.event.pump()` 维持窗口响应，**不取走事件**，事件队列留给调用方的循环处理。
- 实现 `env/random_agent.py`：`select_action(state, training=True)` 签名对齐 `docs/INTERFACE.md` §12，无 `save` / `load`；`play.py` / `evaluate.py` 换 DQN 时不需要改调用代码。
- 实现 `play.py`：`--agent random|human`、`--fps`；`human` 模式 `W` / `↑` 直行、`A` / `←` 左转、`D` / `→` 右转、`Q` / `Esc` 退出（相对转向，不是绝对方位）；`--render_mode` 传入非 `human` 直接 `parser.error`。
- `common/config.py` 拆出 `build_parser(parser=...)` 与 `config_from_args()`，原 `parse_args()` 保留为薄封装：入口脚本可以先构造自己的 `ArgumentParser`（带 `--agent` / `--fps`）再交给 `build_parser` 追加全部配置字段，`-h` 一份里同时列出两套参数。
- 新增 `tests/test_renderer.py`（5 项）、`tests/test_random_agent.py`（3 项）、`tests/test_play.py`（3 项）；`README.md` 目录树与「测试」一节同步。
- 跑 Stage 1 全量验收：`docs/STAGE_CHECKLIST.md` 13 项全部 `[x]`，结论 `Passed`（待项目成员确认），`docs/PROJECT_STATUS.md` 同步。
- 修复 `play.py --agent human` 键盘无响应：`env/renderer.py` 建窗后调用 `pygame.key.stop_text_input()` 关闭输入法组合态。根因经行为 A/B 确认——修复前窗口打开后按 W/A/S/D 完全无反应，修复后一打开即可操控（字母键与方向键均可）。
- `play.py` human 模式增加一行控制台提示（按键说明），用于区分「程序卡死」与「正常等待按键」。
- `docs/AI_DEVELOPMENT_RULES.md` §12 新增「待冻结：`epsilon_decay` 的衰减语义」：记录三种方案的换算表（每 step×0.995 / 每 episode×0.995 / 每 step×0.9999）与推荐结论，标注进入 Stage 2 前由 B 选定并写回；`docs/PROJECT_STATUS.md` P1 改为指向该节。
- 修复 `play.py --agent random` 每次运行完全一致的问题：新增 `_pick_seed()`，`--seed` 未传时随机取一个并打印（附复现命令），传了则原样使用（`0` 也按显式取值处理，判据是 `is None`）。该行为**只作用于 `play.py`**，`train.py` / `evaluate.py` 仍严格受 `Config.seed` 控制。`play.py` 文档字符串同步说明。
- **Stage 1 正式关闭**：`docs/STAGE_CHECKLIST.md` 中 Stage 1 验收结论由「`Passed`（待项目成员确认）」改为「`Passed`（10-07 由项目成员确认，可进入 Stage 2）」，13 项全部 `[x]`；`docs/PROJECT_STATUS.md` 阶段总览中 Stage 1 改为 `Passed`，当前 Stage 改为 `Stage 2 - DQN Baseline`（Pending，B 尚未开工）。
- `docs/INTERFACE.md` §12 新增「实现须知」：第 1 条指向 `env/random_agent.py` 作为 `select_action` 签名的参考实现；第 2 条明确禁止硬编码 `state_dim` / `n_actions`，须由 `env.state_dim` / `env.n_actions` 决定，理由为 Stage 4 的 State V2 维度与 V1 不同，写死 `11` 会在切换 `state_mode` 后抛形状错误且报错位置远离原因。变更记录同步。
- `docs/PROJECT_STATUS.md` 新增 P2（随机初始蛇头贴边的演示观感问题、`stop_text_input()` 无法自动化测试），P1 更新为「阻塞 Stage 2 的 epsilon-greedy 实现」与「Stage 2 尚未开工」。
- `docs/INTERFACE.md` §4 补写 **State V2 预定方案**（由占位说明扩写为完整规格）：V2 = V1 11 维 + `food_distance`（归一化 Manhattan 距离）+ `local_ring`（蛇头周围 8 格占用环，顺序随朝向旋转），共 20 维；`state_mode` 取值增加 `"v2"`。写明追加这两类信息的理由（V1 看不见蛇身形状、看不见食物距离）、已知代价（一次加两类则 Stage 4 无法归因，缓解方式是 Stage 7 拆 V2a/V2b 补跑）、维度变化对输入层的影响与 Stage 4 实现要点。整节标注「预定方案，尚未冻结，待团队确认」，并注明属规范变更、实施前按 §20 流程走。变更记录同步。
- `docs/COLLABORATION_RULES.md` 的「Git 建议」节扩写为 **「Git 工作流」**：确定 `main` 为已完成阶段的集成线，各阶段一律从 `main` 开分支、验收通过后合回 `main`、下一阶段再从更新后的 `main` 开分支。含三步命令（开工 / 开发推送 / 合并）、四条纪律（未验收不进 `main`、必须基于最新 `main` 开分支、合并前先 pull、一阶段一人合）与冲突高发文件提示（`docs/PROJECT_STATUS.md`、`memory.md`）。
- **Stage 1 成果合入 `main`**：`git merge --ff-only feature/env` 成功，`main` 由 `1676df6`（仅含包骨架，6 个提交）前进到 `fc04c26`（含 Stage 1 全部代码与文档，18 个提交）。`feature/env` 分支原样保留，未删除。
- `docs/AI_DEVELOPMENT_RULES.md` §21 的 commit hash 禁令收窄：普通代码 / 文档提交仍不记 hash，但 **Git 合并、回滚、tag 这类以提交为对象的操作必须写明涉及的 commit hash**（fast-forward 合并在 `git log` 里不留痕迹，只写「合到某分支的最新提交」无法核实）。`memory.md` 的两条合并 / 推送记录据此补回 hash。
- 新增 `docs/HANDOVER.md`（工作交接与后续安排），供 B / C / D 阅读。含七节：当前进度表、A 已完成的工作（环境建模的逐项设计动机、State V1 的三段结构与两个结构性盲区、工程实现与文件职责、过程中修的两个问题）、State V2 预定方案摘要与待确认点、后续工作安排（责任边界表 + B / C / D / A 各自要做什么 + 阶段依赖图）、接续工作须知（从 `main` 开分支的命令、三条不能踩的线、已知遗留问题）、需要团队确认的三件事、参考文档索引。文档不复制规范正文，只讲设计动机与分工，涉及规范处一律指向 `docs/INTERFACE.md` 等权威文档，避免出现第二个真相来源。
- `README.md` 目录树补上缺失的 `docs/INTERFACE.md` 与新增的 `docs/HANDOVER.md`，并在「项目状态」一节增加接口定义与工作交接的入口。
- 全量核查文档一致性并修订以下问题：`memory.md` 自身 2 处自相矛盾（「后续影响」中 Stage 1 结论仍写「待项目成员确认」；「发现的问题」中 `human` 视觉效果仍写「尚未人工确认」）、`docs/PROJECT_STATUS.md` 当前状态段把已完成的 State V2 设计写成待办、`docs/INTERFACE.md` 与 `QUICKSTART.md` 各有 2 处把状态维度写死（§1 API 表的 `shape (11,)` 与 `env.state_dim` 的 `11`）、`README.md` 的网络说明写死「11 维输入」、`QUICKSTART.md` 缺 State V2 线索、两处分支合并记录未写实际 commit hash、`docs/INTERFACE.md` 变更记录表行序非时间序。详见「发现的问题」。
- `docs/AI_DEVELOPMENT_RULES.md` §21「日志规则」新增「**追加时回头核对**」：同日追加前必须先扫一遍已有的「发现的问题」与「后续影响」，把被本次操作推翻或已解决的句子就地改掉，并说明这两段属于当前状态、而「操作内容」中的阶段性结论属于合法历史不受此约束。

涉及文件：
- `docs/AI_DEVELOPMENT_RULES.md`、`docs/PROJECT_PLAN.md`、`docs/INTERFACE.md`、`docs/PROJECT_STATUS.md`、`docs/STAGE_CHECKLIST.md`、`docs/COLLABORATION_RULES.md`、`docs/HANDOVER.md`、`README.md`
- `common/config.py`、`env/snake_env.py`、`env/renderer.py`、`env/random_agent.py`、`play.py`
- `tests/test_snake_env.py`、`tests/test_renderer.py`、`tests/test_random_agent.py`、`tests/test_play.py`、`conftest.py`、`smoke_test.py`、`QUICKSTART.md`、`requirements.txt`

执行 / 验证：
- 全仓库检索 `done`、`reward, done`、`done, info`，确认无残留。
- 在 `snake-rl` 环境实跑 `common/config.py`：21 个字段默认值正确；`parse_args(['--initial_head','4,6','--seed','43'])` 正确覆盖且未传入字段不变；`--initial_head 4` 被 argparse 拒绝（exit 2）；`dataclasses.asdict()` 输出可直接 JSON 序列化。
- 在 `snake-rl` 环境实跑 `pytest` 全量：52 passed in 4.29s（环境 41 / 渲染 5 / 随机策略 3 / play 3）。
- 在 `snake-rl` 环境实跑 `play.py` 真实入口：`python play.py --fps 400 --initial_head 5,5` → `episode 结束（撞墙或撞蛇）：score=0  steps=12`，exit=0，窗口正常创建与关闭。
- 在 `snake-rl` 环境复跑 `smoke_test.py`（config 改动后）：6/6 通过，exit=0。
- 合成事件测试 `_wait_for_action()`：`K_d → 2`、`K_w → 0`、`K_q → None`，事件循环逻辑无误。
- 键盘诊断（用户实机按键）：五个按键的 `keycode` / `scancode` 全部正确（`w=119/26`、`a=97/4`、`s=115/22`、`d=100/7`、`q=113/20`），排除输入法吞键与焦点问题在修复后的存在。
- 行为 A/B（用户实机）：修复前 `play.py --agent human` 完全无响应；修复后一打开即可用字母键与方向键操控。
- 复现 `play.py --agent random` 三次：初始蛇头恒 `(0, 8)`、食物恒 `(6, 6)`、恒定 3 步结束。300 个种子统计：最小 1 步、中位数 6 步、最大 66 步、均值 11.0 步。
- 修复后实测种子行为：不传 `--seed` 连跑三次得种子 108758 / 106174 / 897872、步数 9 / 20 / 87；`--seed 7` 连跑两次均为 1 步；`--seed 0` 连跑两次均为 12 步。`pytest` 54 passed（`tests/test_play.py` 由 3 项增至 5 项）。
- 复核 `docs/INTERFACE.md` §4 的 State V2 与仓库既有代码的口径一致性：`local_ring` 中「前 / 右 / 左」三格与 `danger_straight` / `danger_right` / `danger_left` 的对应关系逐一对齐；蛇尾格的取值沿用 §4「碰撞判定」的蛇尾例外，两边都按「非占用」处理，不产生同格不同义。
- 核对 A 名下的全部工作项（`docs/PROJECT_PLAN.md` 各 Stage 的负责人标注 + `docs/INTERFACE.md` §12 责任边界表）：除 Stage 4 外无未完成项。
- 合并前验证 `main` 与 `feature/env` 的关系：`git rev-list --count main..feature/env` = 18、`feature/env..main` = 0、`git merge-base --is-ancestor main feature/env` 成立，确认是 fast-forward；实跑 `git merge --ff-only` 通过，未产生合并提交。
- 核对 README.md 在 `feature/env` 上的改动区间（首处改动在第 52 行之后），确认「在 `main` 顶部加说明」不会与之冲突。该方案最终未采用，改用直接合并 `main`，理由见后续影响。
- 文档一致性全量核查：检索 `待项目成员确认` / `待团队确认` / `尚未人工确认` / `尚未冻结` / `feature/env` / `state_dim` 等易过期表述，逐份对照 `memory.md`、`docs/PROJECT_STATUS.md`、`docs/STAGE_CHECKLIST.md`、`docs/INTERFACE.md`、`QUICKSTART.md`、`README.md`、`docs/PROJECT_PLAN.md`。确认 `docs/PROJECT_STATUS.md` 阶段总览的 Stage 0 / Stage 1 状态顺序有 P0 段解释、`memory.md` 中 52 passed 与 54 passed 属加测试前后的时间顺序，均非缺陷。

发现的问题：
- `docs/AI_DEVELOPMENT_RULES.md` §9 与 `docs/INTERFACE.md` 对 Environment API 的描述不一致（4 元组 vs 5 元组），已修正。
- `docs/INTERFACE.md` 实现前存在 4 处缺口（初始位置参数缺失、蛇尾例外未写明、`close()` 未列、非法 `reward_mode` 行为未定义），已全部补齐。
- `test_initial_head_without_room_raises` 初版写错：`make_env()` 内部就调用了 `reset()`，`ValueError` 在 `pytest.raises` 之前抛出。已改为先构造环境再在 `pytest.raises` 内 `reset()`。
- epsilon 衰减的三个参数未定义「每步衰减」还是「每 episode 衰减」，语义未定，转入 P1。
- `play.py main()` 初版调用了不存在的 `config.agent` / `config.fps`：`parse_args()` 只返回 `Config`，脚本自有参数被丢弃。已把 `config.py` 拆成 `build_parser()` + `config_from_args()` 解决。
- `play.py` 初版 `run()` 与 `_run_agent()` 各调了一次 `env.reset()`，重复消耗随机数。已把 `reset()` + `render()` 下移到两个 `_run_*` 中，`run()` 只做分发。
- `tests/test_play.py` 初版 `subprocess.run(text=True)` 按 locale（GBK）解码，子进程输出 UTF-8 导致 `UnicodeDecodeError`。已在 `run_play()` 中固定 `encoding="utf-8", errors="replace"`。这是 Windows 管道捕获的问题，真实终端显示中文正常。
- `play.py` 在 `env/renderer.py` 之前就 `import pygame`，导致 `PYGAME_HIDE_SUPPORT_PROMPT` 失效、启动横幅漏出。已在 `play.py` 顶部自行设置该环境变量。
- `human` 模式的视觉效果超出自动测试范围（非缺陷，测试覆盖边界）：自动测试只能覆盖到「能建窗、`draw()` 不抛异常」，画面内容由 `rgb_array` 的帧测试间接覆盖（两者共用 `draw()`）。已由项目成员实机游玩确认，见「执行 / 验证」。
- `play.py --agent human` 键盘完全无响应（已修复）：中文输入法组合态吞掉按键，Windows 发出的 `WM_KEYDOWN` 中 `wParam` 为 `VK_PROCESSKEY` 而非真实虚拟键码，`KEYS[event.key]` 因此查不中。修复方式是建窗后 `pygame.key.stop_text_input()`。
- 定位过程中一度误判：先观察到 `TextEditing`（IME）事件，加 `stop_text_input()` 后消失，据此认为已定位；预热重测后发现该事件只是**进程内第一次建窗的一次性 IME 初始化**，与 `stop_text_input()` 无关，该证据无效并已收回。最终结论由**行为 A/B** 确立（修复前不响应 / 修复后一打开即可操控），而非由事件计数确立。
- `play.py --agent random` 每次运行完全一致（已修复）：`Config.seed` 默认 42，同时喂给 `SnakeEnv` 与 `RandomAgent`，故初始蛇头恒为 `(0, 8)`、食物恒为 `(6, 6)`、恒定 3 步撞死。经 300 个种子统计，「3 步就死」本身属随机策略正常范围（中位数 6 步，33.3% 的局 ≤3 步），异常的是「每次完全相同」。
- 随机初始蛇头允许落在边缘，且初始朝向恒为向右，因此约 10% 的开局蛇头位于最右列，直行即撞墙。`--seed 7` 恰好命中该情形，整局只有 1 步。属合法随机结果，但对演示观感不利，如需改善需调整 `_random_head` 的取值域。
- 文档一致性全量核查发现以下问题（均已修订）：
  - **`memory.md` 2 处自相矛盾**：「后续影响」中 Stage 1 结论仍写「待项目成员确认」、「发现的问题」中 `human` 视觉效果仍写「尚未人工确认」，两处都已被同一份文档更靠后的记录推翻。根因是同日反复追加时只写新的、没回头改旧的。已据此在 `docs/AI_DEVELOPMENT_RULES.md` §21 增设「追加时回头核对」规则。
  - **`docs/PROJECT_STATUS.md` 当前状态段**写「A 可并行进行 Stage 4 状态方案的纸面设计」，但该设计已完成，读起来像待办。
  - **状态维度被写死 5 处**：`docs/INTERFACE.md` §1 的 API 表 `shape (11,)` 与 `env.state_dim # 11`、`QUICKSTART.md` 的同两项、`README.md` 的「11 维输入的小型 MLP」。§4 已定义 `state_mode="v2"` 为 20 维，这些写法与 §12「实现须知」第 2 条（禁止硬编码 `state_dim`）自相削弱 —— 文档自己写死维度，却要求代码不许写死。
  - **`QUICKSTART.md` 通篇无 State V2 线索**：速查页是全组对齐用的，组员查它无从得知维度会变。已补 State V2 一行摘要与「不要写死 `11` / `3`」的警示。
  - **合并记录写成了不可核实的表述**：`memory.md` 与 `docs/PROJECT_STATUS.md` 只写「`feature/env` 的最新提交」，一旦 `feature/env` 再前进就无法核实当时合到了哪。已在两处都补上具体 commit。
  - **由此暴露并修复 §21 自身的规则漏洞**：§21 原禁止记录任何 commit hash，理由是「`git log` 已是权威记录」；但 fast-forward 合并在 `git log` 里不产生合并提交、不留痕迹，该理由在此场景不成立——规则与「可核实」直接冲突。已把禁令收窄为「普通提交不记 hash，Git 合并 / 回滚 / tag 必须写明 hash」。`memory.md`「操作内容」中既有的「提交并推送 `1091cfd ...`」按新规则不再违规，未删除。
  - **`docs/INTERFACE.md` 变更记录表行序非时间序**：「新增第 12 节」排在「第 12 节新增实现须知」之后。已重排。
  - 另核对确认**不是**问题、无需修改的有：`memory.md`「操作内容」中按时间顺序记录的「结论 `Passed`（待项目成员确认）」（后续已有条目说明改为已确认，属合法历史）、`docs/PROJECT_STATUS.md` 阶段总览中 Stage 0 `In Progress` 而 Stage 1 `Passed`（P0 段已解释原因）、`docs/INTERFACE.md` §12 的「（V1 为 11）」已带限定故不改。

后续影响：
- Stage 1 环境代码全部完成，验收 13 项全通过，10-07 由项目成员确认，结论 `Passed`，可进入 Stage 2。成果已合入 `main`。
- `stop_text_input()` 的效果无法自动测试（需要真人按键），回归风险由人工验证承担。
- 进入 Stage 2 前需由 B 冻结 `epsilon_decay` 的语义与默认取值，决策方案已写入 `docs/AI_DEVELOPMENT_RULES.md` §12。B 尚未开工。
- 初始蛇头是否避开边缘尚未决定，涉及 `env/snake_env.py` 的 `_random_head` 与既有测试，需用户确认后再动。
- Stage 0 仅剩「所有成员理解接口」（`[~]`，待团队确认），不阻塞 Stage 1。
- State V2 方案已按预定方案写入文档，Stage 4 可直接依此实施。若其他成员有不同意见，改动点集中在 `docs/INTERFACE.md` §4，尚未冻结，改动成本低。
- A 的待办边界（经核对）：**当前可做的只有 Stage 4 的状态实验**，但依赖 Stage 2（DQN）与 Stage 3（`train.py` / `evaluate.py` 统一框架）先行。其余 Stage（3 / 7 / 8）A 均为参与角色，Stage 6 不参与实现。
- Stage 5 的 Reward Shaping **不安排 A 参与**：`docs/PROJECT_PLAN.md` 中 Stage 5 的负责人只有 D；虽然改动落在 `env/snake_env.py` 的 `_compute_reward()`（A 的责任区），但 `docs/COLLABORATION_RULES.md` 已写明「责任人拥有主要维护责任，不代表其他人不可修改，跨责任区修改前应说明原因」，据此由 D 自行实现并在提交中说明，A 事后 review 即可。本次**未**为该分工新增文档条目——现有规则已覆盖。
- 分支流程已定：**B / C / D 开工一律从 `main` 开分支**，不再提「从 `feature/env` 开」的旧说法。上一轮答复中「先不合 `main`、改在 `main` 加一行 README 说明」的建议已作废：把流程定为「`main` 即集成线」之后，正确处理是**直接把 Stage 1 合进 `main`**，说明本身失去意义，且加说明反而会让 `main` 与 `feature/env` 分叉。

## 10-09

操作类型：Code / Docs / Test / Git
结果：Partial

操作内容：
- 按用户已确认的方案，将 `Config.epsilon_decay` 默认值从 `0.995` 改为 `0.9999`，并补充按训练环境步衰减的注释。
- 冻结 epsilon 规格：起点 `1.0`、下限 `0.05`，每成功完成一个训练环境步骤后衰减一次；包含预热与终止/截断的最后一步，跨局延续，评估不衰减。
- 同步开发规范 §12、接口定义 §10、交接文档和项目状态，移除已解决的 epsilon 决策阻塞；Stage 2 记录为配置前置已完成、算法待实现，未通过阶段验收。
- 从本地 `main` 创建并切换到 `codex/dqn`，用于本次修改及后续 B 的开发。
- 按用户要求完成第三步的 Git 分支准备核查：执行 `git fetch origin`，确认当前开发分支已基于最新远程 `main`；Git 准备检查结果 `Passed`。

涉及文件：
- `common/config.py`、`docs/AI_DEVELOPMENT_RULES.md`、`docs/INTERFACE.md`、`docs/PROJECT_STATUS.md`、`docs/HANDOVER.md`、`memory.md`。

执行 / 验证：
- 本机 `python3` 配置专项检查：默认值、CLI 默认与显式覆盖、实例隔离、JSON 存档、help 均通过。
- 数学公式核验：默认值下完成 29,956 次衰减后达到下限；尚未实现或测试实际训练中的衰减逻辑。
- `python3 smoke_test.py`：5/6 通过，第三方依赖检查因缺少 `matplotlib` 失败，退出码 1。
- `git diff --check`：通过。
- `git status --short --branch` 确认当前为 `codex/dqn`；`git rev-list --left-right --count HEAD...origin/main` 返回 `0 0`，无提交差异；`git merge-base --is-ancestor origin/main HEAD` 成功。现有修改仍在工作区，尚未提交或推送。

发现的问题：
- 当前 Python 环境缺少 `matplotlib`，完整依赖自检未通过；本次未修改依赖环境。

## 10-10

操作类型：Code / Docs / Test / Train / Evaluate / Experiment / Other
结果：Passed（组件历史测试及本次训练/独立评估完成；未新增或运行测试套件）

操作内容：
- 按用户要求补齐 evaluate.py，使用 checkpoint 配置加载多模型，以同一评估种子列表运行纯贪心 DQN 和可选 Random，保存逐局 CSV、来源配置和评估摘要；模型不被修改，环境配置不一致时拒绝同组比较。
- 同步 QUICKSTART、README、接口、状态及阶段清单，说明默认 50 局和共同评估命令。
- 按用户要求执行 `python3 -m pip install -r requirements.txt`，将六项项目依赖及所需间接依赖安装到当前系统 Python 3.10；安装成功。
- 完成第四步：新增 `algorithms/networks.py`，实现两层隐藏层的 QNetwork，按环境维度构造网络，支持单状态/批量 Tensor，输出原始动作价值。
- 完成第五步：新增 `common/replay_buffer.py`，实现容量覆盖、状态复制和独立随机数采样，分别保存 terminated/truncated，采样返回六个 NumPy 数组组成的 dict。
- 新增组件及集成测试，同步接口定义、速查页、目录说明、交接文档和阶段清单；第四/第五步完成，完整 DQN 算法未标为通过。
- 按用户要求完成第六步和第七步：新增 DQNAgent，复用 QNetwork，实现 epsilon-greedy、Online/Target Network、Bellman target、Smooth L1 loss、Adam 更新及 checkpoint。
- 新增 `on_env_step(training=True)`，在成功完成环境步骤后计步和衰减；目标网络按成功梯度更新次数同步，预热期通过 `update(None)` 跳过更新。
- checkpoint 恢复网络、optimizer、配置、epsilon、计数与动作 RNG，校验网络结构并保留加载方的设备；环境与回放池状态由训练框架另行管理。
- 同步接口、配置注释、速查页与阶段清单；Stage 2 的 11/13 项已满足，长期稳定性和相对 Random 的性能仍未判为通过。
- 按用户要求补齐第八步中的训练循环与基本日志：新增 `train.py`，逐步调用选动作、环境交互、回放存储、epsilon 计步衰减及预热后网络更新；局末记录指标并延续 RNG 重置环境。
- 新增 `common/utils.py` 设置 Python/NumPy/Torch/CUDA 种子，新增 `common/metrics.py` 新建独立 run 目录、逐局写入并 flush CSV、保存配置及训练摘要。
- 实现局数/精确环境步预算、周期/结束模型保存、Ctrl+C 中断记录和失败摘要；步数预算耗尽的未完成局单独标识，完整局用于汇总，训练摘要不当作评估结果。
- 补充短程调试与三 seed 同预算训练命令、日志含义和后续评估步骤；未实施独立 evaluate，也未标记 Stage 2/3 通过。

涉及文件：
- `evaluate.py` 及上述评估文档。
- `algorithms/networks.py`、`common/replay_buffer.py`、`tests/test_networks.py`、`tests/test_replay_buffer.py`。
- `docs/INTERFACE.md`、`QUICKSTART.md`、`README.md`、`requirements.txt`（网络规模注释）、`docs/HANDOVER.md`、`docs/STAGE_CHECKLIST.md`、`docs/PROJECT_STATUS.md`、`memory.md`。
- `algorithms/dqn.py`、`tests/test_dqn.py`、`common/config.py`（同步计数注释）、`docs/AI_DEVELOPMENT_RULES.md`（执行语义与实现进度）。
- `train.py`、`common/metrics.py`、`common/utils.py` 及训练说明/状态文档。

执行 / 验证：
- 本次 evaluate.py：Not Tested，未执行评估或新增测试，没有新的性能结果。
- 解释器：`/Library/Frameworks/Python.framework/Versions/3.10/bin/python3`。numpy 2.2.6 / torch 2.14.1 / pygame 2.6.1 / matplotlib 3.10.9 / pandas 2.3.3 / pytest 9.1.1 安装完成；`python3 -m pip check` 通过。
- `python3 smoke_test.py`：6/6 通过，退出码 0。
- `python3 -m pytest tests/test_networks.py tests/test_replay_buffer.py -q`：33 passed。
- `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest -q`：87 passed，已有环境/渲染/演示入口的回归均通过；未重新人工游玩。
- 实跑 QUICKSTART 新增的组件示例，输出 Q 值形状 `(1, 3)`；核验默认网络参数量为 18,435。
- `python3 -m pytest tests/test_dqn.py -q`：29 passed，显式核验普通/真终止/截断的 Bellman 值、梯度更新、Target 同步以及 checkpoint 加载后继续执行相同更新的一致性。
- 第六/第七步后复跑 `python3 smoke_test.py`：6/6 通过；无窗口全量回归：116 passed。
- 实跑 QUICKSTART 的 DQN 单步示例：成功完成 1 个环境步骤，epsilon 降至 0.9999，预热期 `update(None)` 返回 None。
- DQN 集成检查执行 160 个环境步骤与 129 次梯度更新，loss 均有限。该短程测试不作为正式学习效果或长期稳定性结论。
- `git diff --check`：通过。
- 第八步本次新增训练入口与日志代码：Not Tested，未执行程序或测试；未生成训练模型、日志或性能数据。此前通过的结果不覆盖本次新增代码。

关键结果：
- 100k模型评估均分seed42/43/44分别20.02/19.58/20.88，Random0.04；相较50k分别+1.26/-0.96/+4.70分。三模型均值18.49→20.16，不能确认均已收敛。
- Q 网络、Replay Buffer、batch shape、epsilon-greedy、Bellman 更新、loss/梯度/optimizer、Target 同步及模型存取共 11 项 Stage 2 验收已满足；持续训练稳定性和相对 Random 的得分仍待验收。
- 完整训练/日志与评估入口现已通过实际运行验证，三个100k训练run及共同评估全部完成。

发现的问题：
- 安装期间下载重试及 pip 版本检查遇到 SSL 错误，依赖安装最终成功，自检与依赖一致性检查通过。
- 未发现本轮NaN/Inf或运行异常；收敛仍未确认，seed44从50k到100k的评估均值提升29.05%。


本日追加实验操作：
- 按用户要求逐个复用旧run的Config，从头训练seed42/43/44至100,000步；三个run均completed，每个99,001次更新，记录loss均有限。
- 训练run_id：baseline100k_dqn_statev1_sparse_seed42_20261010_115409_706718_3d8ac8e7、baseline100k_dqn_statev1_sparse_seed43_20261010_115447_684488_624e6bba、baseline100k_dqn_statev1_sparse_seed44_20261010_115525_500394_e6195a47，输出位于results/logs/，每run包含config/metrics/summary/checkpoint。
- 调用evaluate对三个新模型和Random评估种子10000～10049各50局；输出results/evaluations/evaluate_20261010_115603_654649_e7cff81b/，状态completed。
- 核对新旧Config完全一致，前50k内完整局训练记录一致，共同评估种子列表一致；保存comparison_50k_100k.json和.md，记录样本成绩变化与收敛判断限制。
- Stage2最后两项已有训练/评估数据支持，13项条件满足，待成员确认；未进入Stage3，未提交或推送。

本日追加文档同步：
- 操作内容：按用户要求同步 docs/STAGE_CHECKLIST.md 的实际进度，清理 Stage 2 已被实际训练/评估推翻的未验证描述；Stage 3 标记已有 9/11 项功能，明确模型演示与算法切换仍未完成，以及状态/奖励配置和多版本实现的区别。
- 涉及文件：docs/STAGE_CHECKLIST.md、docs/PROJECT_STATUS.md、memory.md。
- 结果：Passed（文档进度同步）；Stage 2 / Stage 3 的正式验收结论仍为 Pending。
- 执行 / 验证：核对现有入口代码、100k 训练摘要及独立评估摘要；git diff --check。本次程序验证为 Not Tested，未重新运行测试、训练或评估。

本日追加公共 Agent 入口统一：
- 操作内容：按用户要求新增 algorithms/factory.py 的 create_agent / validate_agent_config / load_agent；接入 train.py、evaluate.py 及 play.py 的随机策略创建。模型加载恢复 checkpoint 配置、校验网络与环境维度、覆盖设备与环境渲染设置；评估标签按算法生成，未实现算法明确拒绝。
- 涉及文件：algorithms/factory.py、train.py、evaluate.py、play.py、tests/test_agent_factory.py、README.md、QUICKSTART.md、docs/INTERFACE.md、docs/STAGE_CHECKLIST.md、docs/PROJECT_STATUS.md、memory.md。
- 结果：Passed（公共入口实现及验证）；未实现 play.py 模型加载 CLI，未确认 Stage 2 / Stage 3 验收。
- 执行 / 验证：无窗口全量 pytest 130 passed，含14项新增分派/配置恢复/维度拒绝/训练-保存-加载-评估集成测试；测试替身注册后复用同一训练评估循环。既有三seed的100k模型各50局及Random复评共200条CSV记录与原评估完全一致，模型摘要一致，checkpoint SHA-256不变；复评输出位于自动清理的临时目录。git diff --check通过。
- 关键结果：清单Stage 3同步为10/11项，算法勾选仅表示公共分派机制完成；DQN可训练/加载，Random仅评估/演示。环境、Agent方法、checkpoint格式及原始实验数据未修改。

本日追加模型可视化演示：
- 操作内容：按用户要求为 play.py 增加 --agent model / --checkpoint，通过公共 load_agent 恢复模型和运行配置，纯贪心跑一局；模型模式仅允许覆盖 seed/device/render_mode/fps，拒绝环境和训练参数覆盖；校验FPS/seed及路径组合。为自动演示增加Q/Esc退出，将Agent创建放入环境清理保护区。
- 涉及文件：play.py、tests/test_play.py、README.md、QUICKSTART.md、docs/INTERFACE.md、docs/HANDOVER.md、docs/STAGE_CHECKLIST.md、docs/PROJECT_STATUS.md、memory.md。
- 结果：Passed（模型演示实现及自动验证）；Stage 2 / Stage 3正式验收仍为Pending，未提交/合并/推送。
- 执行 / 验证：初轮play专项21 passed / 1 failed，初轮全量146 passed / 1 failed，均为损坏checkpoint在当前Torch触发未捕获IndexError；补齐CLI错误处理后play专项22 passed，最终无窗口全量147 passed。新增17项测试覆盖配置恢复、固定/随机演示seed、纯贪心且无更新、错误参数、损坏文件、Q/Esc/窗口退出与Ctrl+C清理；完整训练→保存→评估→演示的同seed成绩一致。
- 执行 / 验证：真实play CLI加载已有seed42的100k模型，评估seed10000、fps1000，score=22、steps=149，与原评估记录一致；来源checkpoint SHA-256未改变。git diff --check通过。
- 关键结果：Stage 3清单11/11项已有证据；使用 --agent model --checkpoint <路径> 运行模型演示，默认cpu。演示只读模型，训练seed保留，窗口关闭时释放环境。
- 发现的问题：损坏checkpoint的异常提示已修复；本次使用SDL dummy自动验证渲染，未人工确认新模型窗口观感。

本日追加公共加载流程完善：
- 操作内容：按用户要求完成错误提示统一和重复读取消除；新增 common/checkpoint.py，预期读取/格式/恢复失败统一为带来源路径的CheckpointError；play/evaluate CLI统一显示简洁错误，不输出traceback。DQNAgent新增restore_checkpoint(checkpoint)，原load(path)继续可用；factory只读一次文件后直接恢复内存数据。
- 涉及文件：common/checkpoint.py、algorithms/dqn.py、algorithms/factory.py、play.py、evaluate.py、tests/test_checkpoint_loading.py、README.md、QUICKSTART.md、docs/INTERFACE.md、docs/STAGE_CHECKLIST.md、docs/PROJECT_STATUS.md、memory.md。
- 结果：Passed；Stage 2 / Stage 3正式验收仍待成员确认，本次未提交/合并/推送。
- 执行 / 验证：相关专项84 passed，无窗口全量166 passed，含19项新增测试；验证缺失/损坏文件及元数据、权重、optimizer、RNG无效时play/evaluate的错误内容一致，退出码2且无traceback；文件读取次数由2次减至1次，内存恢复零读取，旧load恢复状态与下一次梯度更新一致。
- 执行 / 验证：现有三seed的100k模型与Random以原50局共同种子复评，共200条CSV记录及模型摘要与原评估完全一致，来源checkpoint SHA-256未改变；复评输出位于自动清理的临时目录。git diff --check通过。
- 关键结果：现有checkpoint格式保持version 1，设备与渲染覆盖规则保持兼容；后续注册算法须提供restore_checkpoint内存恢复方法。

本日追加 Stage 2/3 验收与任务重构：
- 操作内容：按用户要求落定两件事。(1) **Stage 2 与 Stage 3 通过验收**：由项目成员在 Windows + conda `snake-rl` 环境独立复验后确认，两阶段验收结论由 `Pending` 改为 `Passed`。确认前未采信文档既有结论，重跑了依赖检查、自检、全量测试与独立评估。(2) **任务重构**：Stage 4（状态实验）负责人由 A 改为 D，与 Stage 5、Stage 7 合并为同一条实验流水线，在 Stage 6 之后执行；Stage 6（Double DQN / Dueling DQN）提前为下一个开工项。阶段编号 0–8 保持不变，执行顺序的权威说明新增在 `docs/PROJECT_PLAN.md` 的「执行顺序」一节，并写明「合并执行不放松单变量纪律」（Stage 4 组固定 `reward_mode=sparse` 只改 `state_mode`，Stage 5 组固定状态只改 `reward_mode`）。A 不再主导任何实验阶段，只保留 `env/snake_env.py` 与 `renderer` 的文件维护责任；State V2 的实现与实验均转由 D 承担。
- 版本操作：本次改动提交在从 `main`（`0d85c61`）开出的分支 `docs/stage-acceptance-and-reassign` 上，未合并回 `main`。
- 涉及文件：docs/STAGE_CHECKLIST.md、docs/PROJECT_STATUS.md、docs/PROJECT_PLAN.md、docs/COLLABORATION_RULES.md、docs/HANDOVER.md、memory.md。
- 结果：Passed（Stage 1 / 2 / 3 全部通过验收；重构已写入文档）。本次为文档变更与验证，**未改动任何代码**，未产生新的训练或评估结果。
- 执行 / 验证：解释器 `C:\Users\panmingdong\.conda\envs\snake-rl\python.exe`（Python 3.10.21），依赖版本与文档记录一致（numpy 2.2.6 / torch 2.14.1+cpu / pygame 2.6.1 / matplotlib 3.10.9 / pandas 2.3.3 / pytest 9.1.1）。`python -m pip check` 无冲突；`python smoke_test.py` 6/6、exit 0；`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m pytest -q` **166 passed**（50.12s），与 B 报告的 166 一致。
- 执行 / 验证：`python evaluate.py --checkpoints <三个 100k 模型> --num_episodes 50 --eval_seed 10000 --compare_random --output_dir <%TEMP%>` 在本机重跑，平均分 20.02 / 19.58 / 20.88，Random 0.04，标准差与最高分与 B 的 macOS 结果**逐位一致**；输出写在仓库外临时目录，`git status` 保持 clean。`python train.py --total_steps 2000 --output_dir <%TEMP%>` 端到端跑通：completed、1001 次更新、loss 有限、exit 0。三个训练 run 的 summary 核对为各 100,000 步 / 99,001 更新 / ε=0.05 / completed，逐局 loss 无 NaN/Inf，除 seed 外配置完全相同。
- 关键结果：Stage 2 验收项 13/13 满足，Stage 3 验收项 11/11 满足（见 `docs/STAGE_CHECKLIST.md`）。100k 模型的评估结论在 Windows 上可复现，跨平台一致。收敛仍未确认（seed43 由 50k 到 100k 下降 4.67%，逐局标准差约 7，模型间差距 0.86 / 1.30 分小于噪声）——该项不属 Stage 2 验收项，仅记录备查；已有的 100k 训练与评估**无需重跑**。
- 发现的问题：Stage 2 / 3 的代码先经 PR #1–#3 合入 `main`、验收在合并之后补办，与 `COLLABORATION_RULES.md`「未通过阶段验收的代码不进 `main`」不符，属既成事实，已记入 `docs/PROJECT_STATUS.md` 备查。渲染相关验证仍依赖人工（新模型演示窗口观感未肉眼确认，`human` 模式需真人按键），不阻塞验收。
- 追加时回头核对：本日早前几条子记录中「Stage 2 / Stage 3 正式验收仍为 Pending / 仍待成员确认」的表述已被本条推翻。那些句子位于各子记录的「结果」字段，属当时操作的阶段性结论，按 §21 保留为历史；本条即为状态更新。
- 复查记录：以上问题的「当前状态」以本条为准——截至本条，无阻塞 Stage 6 开工的问题。

本日追加 P2 数字更正：
- 操作内容：修正 `docs/PROJECT_STATUS.md` P2 第 1 条中初始蛇头位置的两处比例错误，并同步修正 `README.md` Stage 1 的「存在问题」一行（该行在上一子记录抄用了同一错误数字）。原记「约 10% 的开局蛇头位于最右列」「约 3.3% 的 episode 第一步即结束」。更正为：蛇头列取自 `{length-1, …, board_size-1}` 共 8 个取值，故最右列占 `1/8 = 12.5%`；第一步即结束由三类撞墙构成——最右列直行 `1/8 × 1/3 = 1/24`、第 0 行左转朝上 `1/10 × 1/3 = 1/30`、第 9 行右转朝下 `1/10 × 1/3 = 1/30`，合计 `≈ 10.83%`。原 3.3% 只计入了第一类，漏计后两类转向撞墙。推导过程已写入 P2 正文。
- 涉及文件：docs/PROJECT_STATUS.md、README.md、memory.md。
- 结果：Passed（文档数字更正）。**结论方向不变**——仍属合法随机结果、非缺陷、不阻塞任何阶段；仅数字与推导被修正。
- 执行 / 验证：用项目解释器 `C:\Users\panmingdong\.conda\envs\snake-rl\python.exe` 连续 20 万次 `env.reset()` 统计初始蛇头行列分布：最右列 `0.1248`（理论 `0.1250`）、第 0 行 `0.0998`、第 9 行 `0.0995`（理论 `0.1000`）；另统计 Random 第一步即结束的比例 `0.1078`（理论 `0.1083`）。动作 RNG 用独立的 `np.random.default_rng(0)`，与环境自身 RNG 分离，避免共享随机流造成的偏差。本次未改动任何代码，未重跑训练或评估。
- 关键结果：P2 的 12.5% / 10.8% 及推导过程现与 `env/snake_env.py` 的 `_random_head` 实现一致，`docs/PROJECT_STATUS.md` 与 `README.md` 对初始蛇头的描述统一。
- 追加时回头核对：上一子记录的「涉及文件」漏列了该提交实际改动的 QUICKSTART.md、README.md、docs/INTERFACE.md，完整清单为九个文件，见提交 `d82ccd8`；本子记录一并更正。P2 的错误数字早于本日全部改动，非本日引入，但本日将其抄入 README.md Stage 1 行，故在本日修正。
- 复查记录：截至本条，P2 与其在 README 的引用均无遗留错误数字。

本日追加验收分支合回 main（按 §21 记录版本号）：
- 操作内容：按用户要求把验收与任务重构分支合并回 `main`。分支 `docs/stage-acceptance-and-reassign`（基于 `0d85c61`）先推送，再经 `git checkout main && git pull && git merge docs/stage-acceptance-and-reassign` 合入——**快进合并（fast-forward），未产生合并提交**，故按 §21 在此记录涉及的两个提交号。
- 版本操作：`main` 由 `0d85c61` 快进至 `6991369`。分支上的两个提交为 `d82ccd8`（Stage 2/3 验收与任务重构）与 `6991369`（P2 数字更正）。合并后 `main`、`docs/stage-acceptance-and-reassign`、`origin/main` 三者指向同一提交 `6991369`。
- 涉及文件：无新增文件；本次操作只做合并与推送。
- 结果：Passed。`main` 现已包含 Stage 1/2/3 验收结论、Stage 4 责任调整、执行顺序说明及 P2 更正。
- 执行 / 验证：`git pull` 显示 Already up to date；`git merge` 报 fast-forward 并列出九个文件；`git rev-parse HEAD main docs/stage-acceptance-and-reassign` 在推送前三者同为 `6991369`；`git push origin main` 返回 `0d85c61..6991369`。
- 关键结果：`main` 上无未推送提交，工作树 clean。
- 追加时回头核对：上一子记录的「版本操作」称改动「未合并回 `main`」，已被本条推翻；那条描述的是推送当时的中间状态，按 §21 保留为历史，当前状态以本条为准。分支 `docs/stage-acceptance-and-reassign` 未删除，`feature/env` 仍停留在 `7cfb0c8`（已废弃，未见删除需求）。
- 复查记录：截至本条，`main` 与分支内容一致，无遗留待推送内容。

本日追加 Stage 6 算法实现与算法对比实验：
- 操作类型：Code / Test / Experiment / Docs。
- 操作内容：在从 `main` 开出的 `feature/stage6-algorithms` 分支实现 C 部分。
  `DQNAgent` 新增 `network_class` 扩展点；新增 `DoubleDQNAgent`，由 Online Network
  选下一动作、Target Network 评估；新增 `DuelingQNetwork` 与 `DuelingDQNAgent`，
  按 `Q=V+A-mean(A)` 聚合；`factory.py` 注册 `double_dqn` / `dueling_dqn`。
  新增 `experiments/algorithm_experiment/run.py`，仅编排公共 `train()` / `evaluate()`。
- 涉及文件：algorithms/dqn.py、algorithms/networks.py、algorithms/factory.py、
  algorithms/double_dqn.py、algorithms/dueling_dqn.py、
  experiments/algorithm_experiment/run.py、tests/test_double_dqn.py、
  tests/test_networks.py、tests/test_agent_factory.py、
  tests/test_algorithm_experiment.py、README.md、QUICKSTART.md、
  docs/INTERFACE.md、docs/PROJECT_STATUS.md、docs/STAGE_CHECKLIST.md、
  docs/HANDOVER.md、memory.md。
- 执行 / 验证：仓库内 `.venv` 使用 Python 3.10.4、numpy 2.2.6、torch 2.14.1+cpu、
  pygame 2.6.1、pytest 9.1.1。`pip check` 无冲突；`smoke_test.py` 6/6；
  C 专项 39 passed；`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy pytest -q`
  全量 **180 passed**（42.97s）。
- 实验：`debug_algorithm`，3 算法（dqn / double_dqn / dueling_dqn）× seeds 42/43/44，
  每个 run 20,000 环境步；训练 9/9 `completed`。随后用相同评估种子 10000～10019、
  每个模型 20 局统一纯贪心评估，评估 run 为
  `evaluate_20261010_222836_955475_b7e30d7e`。
- 关键结果：20 局均值（3 seed 模型均分再平均）为 DQN 18.20、Double DQN 20.38、
  Dueling DQN 19.65，Random 0.10；结果保存在
  `results/evaluations/evaluate_20261010_222836_955475_b7e30d7e/`，
  汇总见 `algorithm_comparison.json`，训练日志与 checkpoint 在 `results/logs/debug_algorithm_*`。
- 结果：Passed（实现、测试、统一训练/评估链路均完成）；Stage 6 的 13 项技术条件已有证据，
  正式验收仍待项目成员确认。
- 发现的问题：首次尝试 3 算法×3 seeds×100k 正式预算时，本机运行速度明显慢于原 100k
  记录，运行在 DQN seed42 到 48,080 步时主动中断；该无效部分目录已删除，未混入正式数据。
  最终改用 20k 调试预算验证链路，因为完整 E5 正式比较属于 Stage 7。
- 后续影响：`algorithm` 现可切换 `dqn` / `double_dqn` / `dueling_dqn`，三者共用现有
  Replay Buffer、训练循环、checkpoint 与评估协议。短预算均分只用于验收链路，
  不能据此宣称算法优劣或收敛；项目成员确认 Stage 6 后，D 再执行 Stage 4 + 5 + 7。
- 版本操作：实现与结果提交在从 `main` 开出的 `feature/stage6-algorithms` 分支，
  实现提交为 `31114dd`；已创建轻量标签 `archive/c-stage6-implemented` 指向该提交，
  用于固定 C 部分版本。远端推送因 GitHub 连接失败尚未完成。

## 10-14

操作类型：Git / Docs / Test
结果：Passed

操作内容：
- 远端状态核对：`git ls-remote` 与 `git fetch` 复核 `origin`。`feature/stage6-algorithms`
  的推送已于 10-10 22:35 成功（remote-tracking 记录更新至 `6c70afe`），远端现仍为该提交；
  六个版本标签均已存在于远端且指向与本地一致；本地无任何未推送提交。
- 本地复验：`.venv`（Python 3.10.4）`pip check` 无冲突、`smoke_test.py` 6/6、
  无窗口全量 `pytest -q` 180 passed。

版本操作：
- 10-10 条目「版本操作」中「远端推送因 GitHub 连接失败尚未完成」描述的是推送当时的中间状态，
  按 §21 保留为历史；**当前状态以本条为准**——C 实现分支与全部版本标签已在远端固定：
  `archive/a-stage1-env`=`7cfb0c8`、`archive/b-stage2-3-dqn`=`2ea7906`、
  `archive/c-stage6-implemented`=`31114dd`、`archive/docs-stage-acceptance`=`6991369`、
  `archive/main-stage3-accepted`=`f132e86`、`baseline/c-stage6-start`=`f132e86`。
- 本条更正记录提交建立在 `6c70afe` 之上；仅追加记录，代码、测试与实验结果未改动。

涉及文件：
- `memory.md`

关键结果：
- 各成员版本均可由远端恢复：`main`=`f132e86`、`feature/env`=`7cfb0c8`、
  `codex/dqn`=`2ea7906`、`docs/stage-acceptance-and-reassign`=`6991369`、
  `feature/stage6-algorithms`=`6c70afe` 及本条记录提交。

复查记录：
- 截至核对时点，各分支（含 C 分支 `6c70afe`）本地与远端一致。

## 10-15

操作类型：Git / Docs
结果：Passed

操作内容：
- 按用户（C）要求把 `feature/stage6-algorithms` 合并回 `main`：先创建备份分支
  `backup/main-pre-stage6` 指向合并前的 `main`（`f132e86`），再执行快进合并。

版本操作：
- 备份：`backup/main-pre-stage6`=`f132e86`；该提交此前已由标签 `archive/main-stage3-accepted`
  与 `baseline/c-stage6-start` 锚定。
- `main` 由 `f132e86` 快进至 `4037702`（fast-forward，未产生合并提交，58 个文件）。
  合并涉及提交：`31114dd`（Double DQN / Dueling DQN 实现与调试实验结果）、
  `6c70afe`（archive tag 记录）、`4037702`（远端核对与推送状态更正记录）。
- 本条记录提交建立在 `4037702` 之上；本次推送范围：`main`、`backup/main-pre-stage6`、
  `feature/stage6-algorithms`。

涉及文件：
- `memory.md`

关键结果：
- `main` 现包含 Stage 6 的实现、调试实验结果与全部记录；Stage 6 的验收确认状态以
  `docs/PROJECT_STATUS.md` 为准（合并时该文档仍记录为「待团队确认」，确认后按流程更新）。

复查记录：
- 本次推送：`feature/stage6-algorithms` `6c70afe..4037702`；`main` 由 `f132e86`
  快进至本条记录提交；`backup/main-pre-stage6` 新建于 `f132e86`。推送后本地与远端一致。

## 10-18

操作类型：Code / Test / Train / Evaluate / Docs / Fix
结果：Passed（D-01至D-07实现与接受的正式实验、分析完成；D-05两次失败保留，Stage7技术项具备证据，正式验收待团队）

操作内容：
- 用户要求将 D 的大纲追加至 ppt.md，并统一 A/B/C/D 格式；本次仅整理文档，不修改代码或原始实验数据。
- 汇总为 29 页：A 1–5、B 6–12、C 13–19、D 20–29；依据已有 V1 接口补齐原稿缺失的第 5 页，保留队友页码、分工与实验数值。
- 每页统一七项：核心信息、放置内容、建议图示、讲述重点、建议讲稿、建议时长、资料来源；增加图表链接、排练压缩建议。
- 明确 B 历史环境基线、C 20k 调试、D 当前正式实验的边界；区分逐局 SD 与跨模型 SD、Score 与 Return；收敛、稳定性和机制推断保持限制。
- 同步 PROJECT_STATUS 与个人报告大纲入口；本次不表示实际 PPT、报告或 Demo 已制作，也不自动改变团队验收状态。
- 用户随后要求约10分钟讲完：ppt.md 改为12页主讲，单页内容共570秒，另预留30秒换人/翻页；分工为A 1–3、B 4–5、C 6–7、D 8–12，补充短讲稿与计时排练说明。
- 原29页保存至docs/PPT_FULL_OUTLINE.md，并调整归档相对链接；主讲保留当前正式状态、奖励、探索、算法及最终五seed结论，历史数据、详细消融和测试审计转答辩备用。
- 最后一页包含10秒真实运行展示占位，尚未录制视频，不新增现场Demo耗时；同步个人报告大纲与项目状态入口，不改代码、模型、数据或验收状态。
- 用户要求最终模板直接交给其他智能体：ppt.md 转为自包含制作prompt，保留12页、单页时长、分工、全部主讲统计和事实限制；删除本地资料长路径、开发记录、冗余讲稿及备用材料清单。
- 补充PPTX交付、16:9中文学术排版、可编辑统计图和演讲备注要求；无素材时棋盘须标示意，不伪造运行截图或训练曲线。原29页素材归档保留，实际PPT由后续智能体制作，本次不改程序或实验结果。
- 用户明确要求由本助手实际制作：按ppt.md生成deliverables/Snake_RL_10min_editable.pptx与Snake_RL_10min_preview.pdf，共12页、中文备注12份，570秒内容+30秒预留，保留原生文字、示意图、2张表格及3张带SD误差棒的图表/嵌入工作簿。
- Artifact运行库/依赖加载工具未提供，未安装替代包；改用本机WPS PowerPoint兼容COM与OOXML。先探测导出能力，AddChart接口失败后以标准图表XML和嵌入xlsx实现原生图表。未声称在微软PowerPoint中验证。
- 修复初次包检查发现的Content_Types默认命名空间和第9页SD脚注；最终在WPS重新打开，导出PDF和12张预览，逐页查看。没有真实模型录像，棋盘均标环境示意，不冒充运行结果。
- 生成源码、探测与检查记录保留在.ppt_build/，交付文件单独放deliverables/；更新状态说明PPT已实际生成，但报告/Demo和团队验收仍待，不自动标记阶段Passed。
- 用户确认自己为 D，明确要求先完成奖励部分；固定 V1 + DQN 实现，不开展 V2、探索或正式综合实验。
- 跨 A 的环境责任区补充 distance / distance_step：距离差按同一颗旧食物计算，系数默认 0.1，
  step_penalty 默认 0.01；碰撞距离为零，步惩罚含终止/截断最后一步，reset 全零。
- 新增系数校验、CLI/配置/checkpoint 存档；旧 sparse checkpoint 缺失新字段时沿用默认值。
- 训练与评估追加四项逐局累计奖励，摘要记录完整局分项均值；同组评估校验奖励系数一致。
- 新增 reward_experiment 编排和 plot CLI：复用公共 train/evaluate，模式间分组评估、相同种子、
  统一步数预算；保存唯一目录及中断/失败状态、相对路径 manifest、逐 seed CSV 和原始日志。
- 绘图按环境步分箱，剔除不完整局，空箱不补零或插值，展示训练 Score/Return 与评估得分。
- 新增 49 个测试并更新奖励方案、接口、接手命令与阶段记录。
- 按 D 要求整理 docs/D_WORK_SUMMARY.md，集中记录第一项奖励工作、设计动机、贡献边界、
  实际验证与原始产物链接、PPT 页面提纲/讲稿及后续追加模板；在接手指南和状态页增加入口。
  本次成果整理只更新文档，沿用已执行的验证记录，未重跑训练或测试，不新增性能结论。
- 用户继续要求完成下一项 D 工作，实施 D-02：V2 20 维状态与 E2 状态对比；基于 A 的预案定稿，
  保留 V1 前 11 维，增加归一化当前食物距离和随朝向旋转的八格局部占用环。
- 修正预案“食物刷新后的距离仍为零”的不一致；下一状态描述新食物，奖励仍比较旧食物。
- 修复 _advance 移入旧蛇尾格时 occupied 漏掉新头的问题：先移出旧尾，再加入新头；新增连续尾格移动测试。
  该修复可能影响历史轨迹，本次 V1/V2 六模型全部在当前环境从头训练，不使用旧基线成绩充当对照。
- 新增 state_experiment 的编排/绘图入口，复用公共 train/evaluate；提取共享绘图，奖励原 CLI/API 保留。
- 新增 37 项状态测试、STATE_EXPERIMENT.md，并将正式数据、限制与 PPT 讲稿追加到 D_WORK_SUMMARY 第 10 节。
- 用户同意继续正式奖励任务，完成 D-03：固定 V2 + DQN、系数 0.1 / 0.01，在当前环境重训三模式各三 seeds。
- 增加 --jobs CPU 独立进程选项，每个进程单 Torch 线程，默认串行不变；用相同小配置验证串行/并行指标一致。
- 新增行为复放工具：完整蛇身/朝向/食物重复才记循环，统计墙撞、自撞、超时、未进食步数，保存每类首次出现的真实局面与轨迹。
- 每次行为分析新建目录，逐局核对原评估记录并验证来源 checkpoint 哈希；不匹配则拒绝产生完成摘要。
- 将正式分项表、负结果、行为证据、局限与 PPT 讲稿追加到个人汇总第 11 节，更新指南与状态。
- 用户要求继续下一项工作，完成 D-04：固定 V2 + DQN + sparse，只比较 0.9998 / 0.9999 / 0.99995 衰减。
- 新增探索编排、绘图与 21 项测试，复用 train/evaluate，覆盖真实衰减计步、评估不衰减、串并行与中断状态。
- 三组均从头训练，未复用历史模型；逐条审计实际 epsilon 和训练预算，生成三张正式图并追加个人汇总第 12 节。
- 共享绘图按候选数量循环配色，避免超过三组漏画；探索 Return 不使用跨奖励定义的标签。
- 用户要求继续下一任务并完整留档，启动 D-05 / Stage 7 E5：固定 V2 + sparse + 0.9999，三算法各三训练 seeds、100k 步。
- 跨 C 的实验编排责任区增加可选 Config、CPU 并行、正式协议和新评估种子复核；不改算法实现。
- 训练前新增 docs/ALGORITHM_EXPERIMENT.md，冻结开发 seeds 10000-10049、复核 seeds 20000-20049，按开发均分选候选且不按复核重选。
- 原有与新增编排测试先运行 19 passed（15.05s）；后续训练与验证结果在本日条目继续追加。
- 新增算法审计工具，导出逐 seed 比较表、参数量、时长和来源模型指纹；增加篡改数据拒绝测试。
- 新建 docs/D_REPORT_PPT_OUTLINE.md，按已完成实验建立报告章节与八页汇报提纲，明确尚未完成的综合任务。
- D-05 首轮 algorithm_v2_sparse_20261018_170549_139360_c7cc027b 失败：Double DQN seed42 在 60,176 步保存 checkpoint 原子替换时 PermissionError / Windows 拒绝访问。
  三个 DQN 与另两个 Double DQN 日志 completed，但网格不完整且未统一评估；失败产物保留，不作为正式排名。
  已申请沙箱外同配置全网格、新目录 algorithm_v2_sparse_retry 从头重跑，不按成绩筛 seed、不从无回放池 checkpoint 续训。
- 获准后启动 algorithm_v2_sparse_retry_20261018_173744_167192_364cf11c，全网格从头训练，失败首轮不删除。
- 沙箱外重跑再次在 DQN seed42 最终保存失败；experiment failed，但旧 summary 停在 running/92322，CSV 已有 100k 步。
  未将失败产物伪装成完整模型。具体文件占用来源未证实，不能断言只是沙箱权限问题。
- 跨公共训练入口补充最多六次 PermissionError 原子替换重试（等待 0.2/0.4/0.8/1.6/3.2 秒），
  只写一次临时快照，不删除旧目标，不重走训练或 RNG；其他错误与持续权限错误仍抛出。
- 修复最终保存失败时 summary 未标 failed，新增 tests/test_checkpoint_save.py 四项测试，4 passed（2.95s）。
  首次指定 tests/test_train.py 的命令因文件不存在而未运行测试，已更正测试路径，不计为通过。
- 保存修复后启动 e5_20261018_174445_393629_8f54c9be，同一九模型协议从头执行；最终全量 319 passed（79.37s）、8 条第三方弃用警告。
- 修复后完整 E5 九模型与两套评估完成，运行审计、生成并检查三图；将正式结果、限制、讲稿和复现路径补入个人汇总第 13 节与报告/PPT 大纲。
- 汇总三次尝试的实际 CSV 步数到 attempts.json，首次导出因系统默认 GBK 读取 UTF-8 失败，显式指定 UTF-8 后完成，未改原始数据。
- 用户确认继续交互消融，启动 D-06：固定 DQN / 默认探索与系数，补跑 V1 distance / distance_step 各三个 seed，预先写明 2x3 矩阵与差中差定义。
- 训练前核对 D-02 V1 sparse 与 D-03 V2 三奖励共 12 份配置，除状态/奖励/seed 外一致，来源 official / completed、同环境版本与预算；明确复用而不扩大独立样本数。
- 新增状态 x 奖励聚合审计、配对差中差和三图生成工具；不改环境、算法或训练逻辑，补齐 V1 两种 shaping 六模型。
- 完整矩阵审计后把六格、逐 seed、交互与限制追加到个人汇总第 14 节；报告/PPT 提纲扩展为九页，单列交互页，不把 E6 最终确认写成完成。
- 用户要求继续，启动 D-07 / E6：训练前冻结 DQN+V2+sparse+0.9999，复用 E5 接受的 seeds42/43/44，新训45/46，最终测试固定30000-30049。
- 新增 FINAL_EXPERIMENT.md，声明新增200k步、三模型复用、开发复评重复性与五seed统计口径；测试前固定seed42入口，不按测试择优，不启动Stage8。
- 实施E6编排与逐seed绘图，复用已有审计；正式训练和两套评估后补齐个人汇总第15节及十页PPT大纲，保留新测试下降和最弱seed结果。

涉及文件：
- 本次四人大纲整合：ppt.md、docs/PROJECT_STATUS.md、docs/D_REPORT_PPT_OUTLINE.md、memory.md。
- 实际幻灯片制作：.ppt_build/、deliverables/Snake_RL_10min_editable.pptx、deliverables/Snake_RL_10min_preview.pdf；同步项目状态与本日志。
- 10分钟版另新增docs/PPT_FULL_OUTLINE.md，保留压缩前完整素材。
- env/snake_env.py、common/config.py、common/metrics.py、train.py、evaluate.py。
- experiments/reward_experiment/、tests/test_reward_shaping.py、tests/test_reward_experiment.py、tests/test_snake_env.py。
- docs/REWARD_EXPERIMENT.md、docs/INTERFACE.md、docs/PROJECT_STATUS.md、docs/STAGE_CHECKLIST.md、README.md、QUICKSTART.md、memory.md。
- docs/D_WORK_SUMMARY.md（D 个人贡献与 PPT 素材汇总）。
- D-02 另涉及 experiments/state_experiment/、experiments/plotting.py、tests/test_state_v2.py、
  tests/test_state_experiment.py、docs/STATE_EXPERIMENT.md；更新奖励脚本的 V2 可用性测试与指南。
- D-03 新增 experiments/reward_experiment/behavior.py、tests/test_reward_behavior.py，更新奖励编排、测试及汇总文档。
- D-04 新增 experiments/hyperparameter_experiment/run.py、plot.py、tests/test_exploration_experiment.py、
  docs/EXPLORATION_EXPERIMENT.md；更新 experiments/plotting.py、个人汇总与项目状态记录。
- D-05 扩展 experiments/algorithm_experiment/run.py，新增 plot.py、analyze.py、tests/test_algorithm_official.py、
  docs/ALGORITHM_EXPERIMENT.md、docs/D_REPORT_PPT_OUTLINE.md；同步个人汇总、状态和速查页。
- 公共 train.py 保存重试与最终失败状态修复，新增 tests/test_checkpoint_save.py；不改算法/环境/奖励/探索逻辑。
- D-06 新增 experiments/reward_experiment/ablation.py、ablation_plot.py、tests/test_state_reward_ablation.py、docs/STATE_REWARD_ABLATION.md；同步个人汇总、大纲、奖励指南、README、速查与阶段记录。
- D-07新增experiments/algorithm_experiment/final.py、final_plot.py、tests/test_final_experiment.py、docs/FINAL_EXPERIMENT.md；更新个人汇总、PPT大纲、状态、清单、README与速查。

执行 / 验证：
- 本次大纲整理：29 页连续，203/203 个统一字段，76 个本地链接存在，代码围栏配对，无制表符与复制残留；关键实验数值核对已有正式结果。
- 逐项比对正式 JSON 的 22 组均值/SD 与相应页面一致，三份大纲/状态文档本地链接检查通过，git diff --check 通过；未提交或推送。
- 本次仅作 Markdown 结构、来源和差异检查，未重跑训练、评估、pytest 或 smoke；333 passed 等为前序已执行记录，不作为本次新测试结果。
- 实际PPT验证：validate_deck.py通过，12页/12备注/3原生图表/3嵌入工作簿/2表格、16组正式统计值一致；嵌入数据与图表缓存相符，12张1600x900页面非空，WPS自动检测溢出候选0且逐页目视通过，pdfinfo确认PDF12页。包结构与几何检查0 findings，未运行项目程序测试或新增实验。
- PPT提示词定稿检查：12页连续、逐页570秒+30秒预留=600秒，16组均值/SD与正式JSON一致；正文不依赖本地结果/文档路径，29页归档仍存在，git diff --check通过。仅文档验证，未重跑测试/训练，未生成PPTX，未提交/推送。
- 10分钟版检查：12页连续、84/84字段齐全，单页时长20/40/50/55/45/50/50/45/60/45/75/35秒，共570秒+30秒预留=600秒；归档29页连续，四份大纲/状态文档141个本地链接存在，16组均值/SD与正式JSON一致，代码围栏和git diff --check通过。本次未重跑程序测试或实验，未提交/推送。
- 系统 Python 为 3.8，另有 3.10 但未装 torch；使用 Anaconda 3.12.7 创建项目 .venv，继承已有包。
- 首次 smoke 5/6（缺 pygame），安装 pygame==2.6.1；初次专项 75 passed。
- 初次含绘图的测试因 Anaconda MKL 与 Torch 的 libiomp5md.dll 冲突中止，未视为通过；
  在本地 .venv 安装 NumPy 1.26.4 非 MKL wheel 解决，未设置 KMP_DUPLICATE_LIB_OK，未修改全局包。
- 最终 smoke_test.py 6/6；SDL dummy 全量 pytest -q：229 passed，21.82s；8 条第三方弃用警告。
- 真实 CLI：三模式各 seed42、total_steps=2000、每模型 3 局，3/3 completed，均 1,001 次更新。
- 输出：results/reward_experiments/debug_reward_20261018_133159_843981_21c52af2/，含 comparison.json/.csv、
  三份训练与评估原始产物；plot --bin_steps 500 生成两张 PNG，已目视检查。
- 复评已有三个 100k sparse 模型及 Random，各使用 seeds 10000-10049；200 条逐局结果的六项摘要
  （均分、标准差、最高分、回报、局长、截断率）与历史一致，三个 checkpoint SHA-256 不变。
- 兼容性输出：results/reward_compatibility/evaluate_20261018_133230_934981_b11c897a/。
- git diff --check 通过；本轮无 Git 提交、推送或分支变更。
- D-02 专项 53 passed；无窗口全量 266 passed（19.99s），smoke 6/6，8 条第三方弃用警告。
- 正式 CLI：state_experiment.run --seeds 42 43 44 --total_steps 100000 --eval_episodes 50
  --eval_seed 10000 --official --experiment state_v1_v2；DQN + sparse，隐藏层 128，线程 1。
- 六模型训练 completed，均 100k 环境步、99,001 更新、epsilon=0.05；共 600k 训练步。
- 每模型评估 seeds 10000-10049，共 300 局，无探索/网络更新/回放写入；两组分别评估再汇总。
- 审核配置仅 state_mode 与 seed 不同、实际步数完整、逐局 loss 有限、奖励分项累计与 Return 一致。
- 正式产物：results/state_experiments/state_v1_v2_20261018_134610_974148_b458c91f/，
  含 comparison.json/.csv、六份训练与评估数据及模型；plot --bin_steps 5000 生成两图，已目视检查。
- D-03 奖励编排专项 17 passed，行为工具 3 passed；SDL dummy 全量 270 passed（50.64s），8 条第三方弃用警告；smoke 6/6。
- 正式 CLI：reward_experiment.run --state_mode v2 --seeds 42 43 44 --total_steps 100000
  --eval_episodes 50 --eval_seed 10000 --official --experiment reward_v2 --jobs 3 --torch_threads 1。
- 九模型均 completed，各 100k 环境步、99,001 更新、epsilon=0.05，共 900k 步；配置仅 reward_mode 与 seed 不同。
- 每模型独立评估 50 局，共 450 局，统一环境种子、关闭探索/更新/回放；检查预算完整、有限 loss 和奖励分项记账。
- 正式目录：results/reward_experiments/reward_v2_20261018_152348_243907_d0be64a1/，保存九模型、原始 CSV/JSON、比较表和两张正式图。
- behavior/analysis_20261018_153547_deb51a8a/ 逐局复放原 450 局，Score/Return/局长/分项/结束标记一致，九模型 SHA-256 不变。
  复放不是新增独立样本；另存 metrics.csv、summary.json、examples.json 和六案例局面图，三张图均目视检查。
- D-04 SDL dummy 全量 291 passed（58.21s），8 条第三方弃用警告，smoke 6/6；共享绘图调整后三项端到端测试通过。
- 正式 hyperparameter_experiment.run：三衰减 x seeds 42/43/44、100k 步/模型、50 局评估、eval_seed=10000、jobs=3、torch_threads=1。
- 九模型 completed，各 100k 环境步/99,001 更新/epsilon=0.05，共 900k 步；配置仅 epsilon_decay 与 seed 不同。
- 全部 15,269 条训练记录 epsilon 符合已完成步数公式，预算之和完整、loss 有限、奖励记账一致。
- 450 条独立评估种子对齐、探索/更新/回放关闭；按原始数据重算各组均值与总体标准差一致。
- 产物：results/exploration_experiments/exploration_v2_sparse_20261018_163701_745710_520966f1/，含九模型、原始数据与三张已目视检查的正式图。
- D-05 原/新增编排专项先 19 passed；加入审计异常测试后专项 26 passed（32.32s），最终全量 315 passed（72.61s）、8 条第三方弃用警告；smoke 6/6。
- 保存修复及更新次数审计边界后专项 28 passed（19.18s），最后全量 319 passed（48.51s），8 条第三方弃用警告；本轮自检 6/6。
- 接受正式 run_id：e5_20261018_174445_393629_8f54c9be，V2 + sparse + 0.9999，三算法各 seeds 42/43/44、100k 环境步/99001 更新/epsilon=0.05。
- 每模型开发 seeds 10000-10049、新复核 seeds 20000-20049，各 50 局；每套另有 Random 50 局，共 1000 条评估，关闭探索/更新/回放。
- analysis/audit_20261018_175556_016801_2c7aa9f6/ 审计 14,348 条训练与 1000 条评估记录，核对累计步数、epsilon、loss、奖励、来源、种子、六项摘要与选优规则。
- 保存 summary.json、20 行逐模型 comparison.csv、attempts.json 与九模型指纹；指纹是审计时 SHA-256，不声称评估前后对比。
- 三次尝试实际步数 560,176 / 300,000 / 900,000，总计 1,760,176；只有最后完整 900k 参与排名，不把重跑算成更多独立训练 seed。
- 三张正式图 training_curves / development_scores / holdout_scores 从原始数据生成并目视检查；未做 Git 提交、推送或分支操作。
- 最后检查五份主文档的 78 个本地链接均存在，git diff --check 通过；Stage 7 仍 In Progress，未自动推进 Stage 8。
- D-06 先完整审计 12 个复用模型、62 个来源指纹；新增专项 7 passed（8.05s），全量 326 passed（53.15s），8 条第三方弃用警告，smoke 6/6。
- 训练 run_id：ablate_20261018_182154_464727_64db71b9，V1 distance / distance_step 各 seeds 42/43/44，100k 步/模型，jobs=3、Torch 线程 1；六模型 completed，各 99001 更新/epsilon=0.05，本轮无保存异常。
- 新增600k训练步、300局评估，环境 seeds10000-10049、纯贪心/无网络更新/回放写入；不使用 E5 复核集调参。
- 聚合 run_id：factorial_20261018_182816_405632_23aee76b，复用 D-02 V1 sparse 三模型与 D-03 V2 三奖励九模型，形成18模型/900条评估矩阵。
- 审计全部 28,721 条训练记录（新增 9,689 条）、900 条评估与93个来源文件指纹；核对跨源协议、配置、checkpoint、预算/更新、epsilon/loss、奖励记账、模型来源与摘要；来源在审计期间未变。
- 产物根目录 results/ablation_experiments/：保留六份新增模型/原始日志、factorial comparison.json/.csv、三张已目视检查的正式图；全部格子截断率0。
- 文档与绘图后再次核对93个来源指纹一致；七份主文档106个本地链接存在，git diff --check通过，未提交/推送或进入Stage8。
- D-07运行前专项7 passed（11.03s）；最终含四图的全量333 passed（54.89s），8条第三方弃用警告，smoke6/6。
- run_id：e6_20261018_184033_503575_81385455。新训练45/46均completed，各100k步/99001更新/epsilon=0.05，复用E5接受的DQN42/43/44，共五模型/500k步对应预算，本轮只新增200k。
- 开发10000-10049与最终新测试30000-30049，五模型+Random各50局/组，共600条本轮执行记录；不把旧模型开发复评当新增独立seed。
- 审计五模型8,013条训练（新增3,263）、600条评估，预算/更新/epsilon/loss/奖励、配置/checkpoint、来源与六项摘要核验通过。
- 13个复用来源文件运行前后SHA-256一致，且E5旧三模型及Random的200条重复开发逐局记录完全复现；四张正式图已目视检查。
- results/final_experiments/e6_20261018_184033_503575_81385455/保留manifest、final_config.json、两新增模型/日志、两评估组与四图；analysis/audit_20261018_184355_953893_304ba2f0/保留审计与12行逐模型CSV。
- 最后检查七份主文档118个本地链接存在、git diff --check通过，未执行Git提交/推送/分支操作；后续只补充E6交叉链接，不改原始数据。

关键结果：
- 奖励实现、分项记账、旧模型加载及实验/绘图链路已有验证；D-01 的旧模型指标一致性是修复尾格前的历史验证，
  D-02 环境修复后不声称所有旧轨迹完全一致，当前状态对比采用同版本重训。
- 调试仅 1 个训练 seed、每模型 3 局，不据此宣称 shaping 提升或算法收敛。
- D-02 正式 Score：V1 18.98/18.60/19.94，V2 22.96/22.22/21.38；均值 19.17→22.19，约 +15.72%。
- 跨 seed 总体标准差 0.56→0.65，平均局长 156.92→182.53，截断率均 0；每 100 步食物数 12.22→12.15。
  因此只报告当前条件下每局得分改善，不宣称稳定性或单位步数效率提高，不单独归因距离/局部环。
- 默认网络参数量 V1 18,435、V2 19,587，差异已记录；状态阶段技术项 10/10 满足，仍待团队验收。
- D-03 Score：sparse 22.19 ± 0.65、distance 19.89 ± 0.15、distance_step 21.31 ± 0.27（ddof=0），
  后两者较基线 -10.37% / -3.94%，三个配对训练 seed 都未超过 sparse。
- distance_step 的 Return 216.16 > sparse 211.87、最高分 43 > 35，但平均 Score 更低；不按跨奖励 Return 或最高分排名。
- 每组 150 局，撞墙 20/24/20、自撞 130/126/130，无超时或完整状态循环，最长连续未进食 42/42/44；不外推普遍不存在循环。
- D-03 V2 固定系数的 shaping 没有提升平均得分；仍保留数据和模型，不删 seed、不为追求正结果临时调系数。
- D-04 快/默认/慢 Score：21.39 ± 0.96 / 22.19 ± 0.65 / 19.94 ± 0.34；快/慢相对默认 -3.61% / -10.13%。
- 两候选三个配对 seed 均未超过默认；快组训练得分先上升并不代表最终贪心策略更好或收敛更快。
- 默认重新训练的逐 seed 均分与 D-03 相同配置一致，不计为更多独立训练种子；当前暂保留默认 0.9999。
- D-05 开发 DQN / Double / Dueling 均分：22.19 ± 0.65 / 19.77 ± 0.74 / 21.01 ± 1.01；
  新复核：21.45 ± 1.49 / 19.89 ± 1.01 / 20.83 ± 0.86，Random 0.04 / 0.12。
- 按预先开发规则保留 DQN，复核排名一致但差距缩小；Double seed44、Dueling seeds43/44 复核高于对应 DQN，不声称逐 seed 占优或更稳定。
- 参数量 DQN/Double 19,587，Dueling 19,716，多 129；实际时长保留，但并行与测试负载不同，不作速度排名。
- D-05 / E5 完成，E6 与交互消融未完成；整体技术/团队验收状态不自动升级，报告与 PPT 提纲明确这些缺口。
- 后续 D-06 已完成交互消融：V1 sparse/distance/distance_step 为19.17±0.56 /17.27±1.50 /19.61±1.56；V2为22.19±0.65 /19.89±0.15 /21.31±0.27。
- distance 的 V1/V2 平均增益 -1.90/-2.30，差中差 -0.40±2.52；distance_step 为+0.44/-0.87，差中差 -1.31±2.25，均为配对总体 SD，不是 CI 或显著性。
- V1 distance_step 的配对差+0.06/+3.14/-1.88；两个交互均有正负 seed，不声称可靠塑形收益、稳定交互或 V2 距离冗余因果机制。
- 当前六格均分最高仍 V2 sparse，维持已有候选；新增6模型与复用12模型计数分开，不把900条汇总记为900条新增评估。
- E6五seed开发22.60±1.19，最终新测试20.76±2.64，Random0.04/0.12；均为跨模型均分总体SD，不是CI。
- 最终测试逐seed：42=22.78、43=20.60、44=16.54、45=19.66、46=24.20；保留seed44下降，未按最高的seed46重选入口。
- 新样本均分较开发低8.14%、跨模型波动更大，不单独归因过拟合或分布转移；平均Return197.56、局长169.12、截断率0，单局最高43不用于选优。
- Stage7技术清单13/13有证据，团队正式验收仍Pending；未进入Stage8，报告/PPT与Demo实际制作尚待。

发现的问题：
- 正式多 seed 奖励、行为与探索分析已完成，Stage 5 技术项满足，正式验收仍待团队确认。
- V2 实现、正式状态实验与分析已完成，待团队验收；Stage 6 的团队确认仍待处理。此次推进来自用户明确指令。
- .venv 为本机继承 Anaconda 的验证环境，不可直接作为跨机器依赖锁定文件。
- Windows checkpoint 替换的具体占用来源未证实；有上限重试与最终失败状态修复已测试，完整正式网格通过，仍不能保证所有文件系统错误均可恢复。
- 两个历史失败目录保留，其中 retry seed42 的旧模型摘要 running 与 CSV 100k 不一致，attempts.json 已登记；不能拿该模型当完整正式结果。
- D-06 的均值差和配对交互方向不一致，只有三训练 seed，不能作显著性判断；V2仍含两类新增特征及1152参数差异，未单独验证距离冗余机制。
- E6虽扩展至五seed，新测试均分仍有16.54-24.20差异且低于开发；未证明收敛或普遍稳定，不能用新测试再挑模型/调参。

后续影响：
- E0-E6及交互消融完成，用户已指定制作并交付12页PPTX/PDF初版；下一项为团队验收、课程报告、真实Demo和四人计时排练。冻结候选DQN+V2+sparse+0.9999与入口seed42已留档，不自动确认阶段Passed。
- 前序状态/奖励/探索基于 DQN 顺序选择，当前算法比较不是各算法独立调参上限；不宣称机制归因或全局最优。
- 前序比较三seed、E6最终五seed，均单预算、预定系数；最终测试已使用，未来继续调参须新保留种子，不宣称显著性、普遍最优或所有shaping均无效。
