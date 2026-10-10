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
