# 项目状态记录

## 当前状态

当前 Stage：`Stage 0 - 工程初始化`

总体状态：`In Progress`

最后更新：`10-07`

---

## 阶段总览

| Stage | 内容 | 状态 | 负责人 |
|---|---|---|---|
| 0 | 工程初始化与接口冻结 | In Progress | 全员 |
| 1 | Snake 环境与状态 | Pending | A |
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

---

## 待完成

- [x] 创建真实代码仓库结构
- [x] 创建依赖环境
- [x] 实现 config
- [x] 冻结 Environment API
- [x] 统一接口口径（4 元组 → 5 元组）
- [ ] 冻结 Agent API
- [ ] 完成 Stage 0 smoke test
- [x] 确定结果保存路径

---

## 当前存在的问题

### P0

1. Stage 0 剩余 2 项中，Agent API 位于 B 的责任区，B 尚未开始提交任何代码，Stage 0 无法通过验收，Stage 1 因此被阻塞。
2. 尚无任何可运行代码，`env/` 等包内仅有 `__init__.py` 占位，`common/config.py` 是唯一有实际内容的模块。

影响：

只能确认项目设计、接口定义、依赖环境与配置管理，不能确认任何环境或算法已实际运行成功。

处理：

1. 与 B 确认 Agent API 的交付安排，或由团队重新指派负责人。
2. 完成 Stage 1 环境实现后更新。

---

## 最近一次测试

测试时间：`10-06`

测试内容：

```text
依赖环境导入与张量互转：numpy / torch / pygame / matplotlib / pandas，
numpy → torch 转换，MLP 前向。
```

结果：

`Passed`

---

## 下一步

推荐只进行 Stage 0。剩余项：

- 冻结 Agent API（B 责任区）
- 所有成员理解接口（需团队确认）
- Stage 0 smoke test（判定标准待澄清，见下）

完成后逐项核对 `STAGE_CHECKLIST.md`，再由项目成员确认是否进入 Stage 1。

**待澄清**：`README.md` Stage 0 完成标准写「项目可正常安装并启动」，但 `train.py` / `play.py` / `evaluate.py` 均为后续阶段产物，Stage 0 阶段「启动」的判定对象需团队确认。

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
