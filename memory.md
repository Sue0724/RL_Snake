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

涉及文件：
- `docs/AI_DEVELOPMENT_RULES.md`、`docs/PROJECT_PLAN.md`、`docs/INTERFACE.md`、`docs/PROJECT_STATUS.md`、`docs/STAGE_CHECKLIST.md`
- `common/config.py`（新增）

执行 / 验证：
- 全仓库检索 `done`、`reward, done`、`done, info`，确认无残留。
- 在 `snake-rl` 环境实跑 `common/config.py`：20 个字段默认值正确；`parse_args(['--seed','43','--learning_rate','0.0005','--render_mode','human'])` 正确覆盖 3 个字段，未传入的字段保持默认；`dataclasses.asdict()` 输出 20 个 key 可直接 JSON 序列化。

发现的问题：
- `docs/AI_DEVELOPMENT_RULES.md` §9 与 `docs/INTERFACE.md` 对 Environment API 的描述不一致（4 元组 vs 5 元组），已修正。
- `README.md` Stage 0 完成标准「项目可正常安装并启动」的判定对象不明确，待团队澄清。

后续影响：
- 接口口径已统一，配置系统可用，可据此实现环境。
- Stage 0 剩余项为 Agent API 与所有成员理解接口，均在 B 侧或需团队确认，Stage 1 仍被阻塞。
