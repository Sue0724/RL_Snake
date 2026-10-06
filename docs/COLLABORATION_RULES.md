# 团队协作规范

## 总原则

项目虽然由四个人分工，但只有一个统一代码库、一个统一环境和一个统一评价体系。

---

## 责任边界

### A

主要负责：

- env/snake_env.py
- renderer
- state representation
- state_experiment

### B

主要负责：

- algorithms/dqn.py
- replay buffer
- target network
- DQN baseline
- 统一训练框架基础

### C

主要负责：

- algorithms/double_dqn.py
- algorithms/dueling_dqn.py
- algorithm_experiment

### D

主要负责：

- reward_experiment
- hyperparameter_experiment
- aggregate analysis
- final comparison

责任人拥有“主要维护责任”，不代表其他人不可修改。

跨责任区修改前应说明原因。

---

## 接口冻结

以下接口确定后，不应随意修改：

- Environment API
- Agent API
- Config key
- metrics 字段
- experiment output 格式

如必须修改：

1. 说明理由。
2. 检查影响文件。
3. 更新文档。
4. 更新所有调用方。
5. 完成集成测试。

---

## Git 建议

推荐分支：

```text
main
dev
feature/env
feature/dqn
feature/double-dqn
feature/dueling-dqn
feature/reward
feature/experiments
```

不要让四个人长期在同一个文件上并行修改。

---

## Commit 原则

一个 commit 尽量只做一类修改。

示例：

```text
feat(env): implement snake collision and food generation
feat(dqn): add target network update
fix(reward): prevent distance shaping from dominating food reward
exp(state): add state v2 comparison
docs: update stage 3 status
```

---

## 合并前检查

至少检查：

- 当前分支能运行
- 不破坏原有目录
- 不存在明显 hard-coded path
- 不覆盖他人实验数据
- README / PROJECT_STATUS 是否需要同步

---

## 冲突处理

发生冲突时优先：

1. 保留已验证接口。
2. 保留正式实验数据。
3. 不要简单选择“Accept Current / Incoming”。
4. 重新运行最小集成测试。

---

## AI 使用规则

Codex / Claude Code 可以：

- 辅助编码
- Debug
- 生成测试
- 检查代码
- 生成实验脚本
- 整理日志
- 解释算法

但不能代替：

- 实际运行验证
- 最终实验判断
- 人工确认阶段完成
- 对实验结论负责

任何 AI 生成的算法公式和代码都需要核对。

---

## 每日同步建议

每次开发完成后更新：

`docs/PROJECT_STATUS.md`

只记录：

- 完成了什么
- 验证了什么
- 发现什么问题
- 下一步是什么

不要写成长篇开发日记。
