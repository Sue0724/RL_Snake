# 项目操作记录

## 10-06

操作类型：Docs / Git
结果：Passed

操作内容：
- 新增 `memory.md` 项目操作日志机制，并在统一 AI 开发规范中加入对应要求，README 同步说明。
- 本地 `Snake-RL/` 初始化 git 仓库（`git init -b main`）并关联远程 `Sue0724/RL_Snake`，将现有 11 份项目文档作为首个 commit 推送至 `main`。
- 从 `docs/COLLABORATION_RULES.md` 的分支建议中删除 `dev`，保留 `main` + `feature/*`。
- 精简 `memory.md`：说明文字、字段要求与记录模板全部迁入 `docs/AI_DEVELOPMENT_RULES.md` §21，本文件只保留操作记录；日期格式改为 `MM-DD`，同日操作合并到同一条。
- 统一日期格式：`docs/PROJECT_STATUS.md` 更新模板改为 `MM-DD - 简短标题`。
- 本机配置 git 全局代理，解决直连 GitHub 不稳定问题。

涉及文件：
- `memory.md`、`README.md`
- `docs/AI_DEVELOPMENT_RULES.md`、`docs/COLLABORATION_RULES.md`、`docs/PROJECT_STATUS.md`

执行 / 验证：
- `git ls-remote origin main` → 与本地 HEAD 一致。
- 全仓库检索 `dev`，确认无其他残留引用。
- `git config --global http.proxy http://127.0.0.1:7890` → 配置后 `git ls-remote` 无需再加 `-c` 参数，访问成功。

关键结果：
- commit `d37ce77`（11 files，2737 insertions）
- commit `d86916d`（2 files，+30 −1）
- commit `63662b3`（2 files，+105 −225）
- 远程 `refs/heads/main` = `63662b3`

发现的问题：
- 直连 GitHub 不稳定，`git push` 多次失败。已通过本机全局 `http.proxy` 解决。

后续影响：
- 后续代码开发应在 feature 分支进行，不直接改 main。
- 本机 git 全局代理指向 `127.0.0.1:7890`；代理程序未运行时 git 将无法联网，撤销命令为 `git config --global --unset http.proxy`。
