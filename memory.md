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
