# D 的奖励实验接手指南

个人贡献、阶段性结论与 PPT 素材见 [D 工作汇总](D_WORK_SUMMARY.md)。本指南主要记录实现规则和运行方式。

## 当前范围

D-01 先固定 DQN + State V1 完成奖励实现与短程调试，D-02 已完成 V2 状态实验。
本次 D-03 固定 DQN + State V2，在尾格占用修复后的同一环境正式比较三种奖励。
用户已同意三个模式各 seeds 42/43/44、每模型 100k 步、50 局独立评估。
系数预先固定为 0.1 / 0.01，不因中途成绩调整。
探索对比现已在 D-04 完成，见 [EXPLORATION_EXPERIMENT.md](EXPLORATION_EXPERIMENT.md)；最终综合实验仍待开展。
Stage 5 技术项满足，正式验收仍待团队确认，不自动判定通过。

## 奖励定义

令 d 为蛇头到食物的曼哈顿距离，单位是格子，不做归一化。
所有方案保持吃食物 +10、撞墙/撞自身 -10；填满棋盘是胜利，无死亡惩罚。

| reward_mode | distance_reward | step_reward |
|---|---|---|
| sparse | 0 | 0 |
| distance | distance_reward_scale * (d_before - d_after) | 0 |
| distance_step | distance_reward_scale * (d_before - d_after) | -step_penalty |

默认 `distance_reward_scale=0.1`，`step_penalty=0.01`。
两系数须有限、非负，且二者之和小于 10。它们是实验起点，不是已验证的最佳系数。
每步量级限制不能保证整局累计 shaping 一定小于食物奖励，仍需检查分项日志。

- 距离差仅在合法移动时计算，移动前后比较同一颗旧食物。
- 吃到食物的一步距离差为 +1；新食物生成不产生距离奖励。
- 碰撞一步距离项为 0；distance_step 的步惩罚仍计入最后一步。
- 截断一步正常计算距离与步惩罚，不额外加入死亡惩罚。
- reset 四个奖励分项均为 0，不产生步惩罚。
- 在当前相对动作规则下，合法移动每次使曼哈顿距离变化 +1 或 -1。
- 本方案是启发式 shaping，不声称具有势函数 shaping 的最优策略不变保证。
- 奖励不改变碰撞、食物生成 RNG、状态或终止规则。

## 启动环境

在项目根目录运行。已有课程 conda 环境时，可激活后使用 `python`。
10-18 本机验证使用项目 `.venv`，可直接使用以下路径：

```powershell
.\.venv\Scripts\python.exe smoke_test.py
.\.venv\Scripts\python.exe -m pytest -q
```

不要直接使用当前系统 PATH 的 Python 3.8；项目要求 Python 3.10+。
本机 `.venv` 继承现有 Anaconda 包，不是可移植环境。跨机器搭建仍按 README 安装依赖。

## 单方案训练

```powershell
.\.venv\Scripts\python.exe train.py --algorithm dqn --state_mode v1 --reward_mode distance_step --distance_reward_scale 0.1 --step_penalty 0.01 --total_steps 2000 --seed 42 --experiment debug_reward_single
```

输出仍使用公共 `results/logs/<唯一run>/`，结束时打印实际目录。
单个模型可通过原有 evaluate/play CLI 加载，奖励参数自动从 checkpoint 恢复。
旧 sparse checkpoint 缺少新增系数时使用默认值；原有奖励行为不变。

## 三方案短程调试

```powershell
.\.venv\Scripts\python.exe -m experiments.reward_experiment.run --seeds 42 --total_steps 2000 --eval_episodes 3 --experiment debug_reward
```

编排脚本复用公共 `train()` / `evaluate()`，不复制训练循环。
同一次比较只有 reward_mode 和训练 seed 改变；所有模式使用同一组训练 seeds。
不同奖励方案分别调用 evaluate，评估环境种子列表相同。
默认算法固定 DQN，拒绝把算法对比混进奖励实验。
现已支持 V1/V2；可显式传入 `--state_mode v2` 重新开展一组奖励对比。
10-18 状态任务修复了移入旧蛇尾时的占用集合错误；之前的奖励调试仍保留为历史，正式奖励实验必须在当前同一环境版本重跑所有模式。
状态、网络宽度、探索、预算或系数不一致的历史 run 不会自动混入。

## 正式比较

根据状态实验，本轮固定 V2；不能把先前 V1 短程调试与本组结果直接归因于奖励变化。
下面使用 3 个独立 CPU 训练进程，每个进程一个 Torch 线程；默认 --jobs 1 保持串行。
已用相同小规模配置验证串行/并行的训练指标和评估汇总一致（时间、run_id 除外）。

```powershell
.\.venv\Scripts\python.exe -m experiments.reward_experiment.run --state_mode v2 --seeds 42 43 44 --total_steps 100000 --eval_episodes 50 --eval_seed 10000 --official --experiment reward_v2 --jobs 3 --torch_threads 1
```

`--official` 要求至少 3 个训练 seed、2 种奖励和每模型至少 20 局评估，并拒绝 debug 名称。
正式标识只是实验协议标签，不表示收敛、显著提升或验收通过。
配置选择可使用另一组评估种子，最终比较再使用预先保留的种子，避免反复调同一批测试局。

## 产物与绘图

每次新建 `results/reward_experiments/<唯一run>/`，不覆盖历史实验：

```text
comparison.json       协议、训练路径、分组评估路径和跨 seed 汇总
comparison.csv        每种奖励、每个训练 seed 的独立评估摘要
logs/<run>/           config.json / metrics.csv / summary.json / checkpoint.pt
evaluations/<run>/    config.json / metrics.csv / summary.json
figures/              运行绘图命令后生成
```

comparison.json 内的训练/评估路径相对该文件所在目录保存，可以随整个实验目录移动。
公共 evaluate 的历史绝对路径仅作来源记录；不作为绘图或重跑的本机路径。
失败与中断会保存对应状态，不能把部分数据当作完整结果。

将路径替换为脚本打印的 comparison.json：

```powershell
.\.venv\Scripts\python.exe -m experiments.reward_experiment.plot --comparison results/reward_experiments/<run>/comparison.json --bin_steps 5000
```

- training_curves.png：Score 与 Return 两张训练曲线；按环境步分箱，先算每个 seed 的局均值，再跨 seed 汇总。
- 不完整局不进入曲线，原始 CSV 仍保留；空箱保留缺口，不插值、不补零。仅所有 seed 都有完整局时画标准差带。
- evaluation_scores.png：独立贪心评估的平均 Score，黑点为各训练 seed 的模型均分，误差棒为模型均分的总体标准差（ddof=0）。
- 训练曲线受探索影响，不能替代独立评估。当前未按训练时点留存独立模型，不能据此严格断言贪心评估收敛速度。

## 分析要点

训练和评估 CSV 均追加 food_reward / death_penalty / distance_reward / step_reward，
它们是本局累计值，和等于 episode_return；摘要中的 mean_reward_components 是完整局的分项均值。
预算耗尽的不完整训练局有明确标志，不参与训练摘要均值。

主要比较独立评估 Score，不用不同定义的 Return 给奖励方案排名。
报告应同时观察平均分、跨 seed 波动、局长与截断率；高局长、低 Score、较多截断可能提示绕圈。
这些指标只是提示，仍需通过 play.py 的模型演示核实行为；死亡标记本身不能区分撞墙和自撞。
无收益或负收益也应保留，不能只挑最好看的 seed 或曲线。

## 失败行为复放

对已完成的 comparison.json 运行：

```powershell
.\.venv\Scripts\python.exe -m experiments.reward_experiment.behavior --comparison results/reward_experiments/<run>/comparison.json
```

输出在该实验的 behavior/analysis_<唯一标识>/ 中，包含 metrics.csv、summary.json、examples.json 和 examples.png。
每次新建分析目录，不覆盖历史分析；只复放已有模型，不训练或改变来源 checkpoint。
使用原评估种子，逐局核对 Score、Return、局长、奖励分项和结束标记；不匹配则拒绝输出完成摘要。

- wall/self：按最后一次尝试落点区分撞墙或自撞，不改变环境 API。
- timeout/win：区分到达上限与填满棋盘。
- exact cycle：固定贪心策略下，完整蛇身、朝向和食物坐标重复；不是仅凭压缩观测或局长判断。
- max_steps_without_food：最长连续未进食动作数，不包含吃食物的那一步。
- zero_food_timeouts：整局没有吃食物且超时；与“高分但活到上限”分开统计。
- 案例按固定顺序选取每类结局和完整循环的首次出现，保留来源模型与完整轨迹；只作诊断，不代表性能抽样。
- 图中显示最后一个动作前的真实局面，箭头表示尝试动作；全量分析的分母仍包含全部评估局。

这些计数反映本批种子下的观察，未发现循环不意味着所有可能开局都不存在循环。

## D-03 正式结果（10-18）

三模式各 3 seeds、每模型 100k 步及 50 局独立评估已完成：共 900k 训练步、450 局评估。
另对同一批 450 局逐局复放验证，不将复放次数计为新增独立样本；九个来源模型哈希未变。

| 方案 | seed42 | seed43 | seed44 | 跨 seed 均值 ± 总体标准差 | 相对 sparse |
|---|---:|---:|---:|---:|---:|
| sparse | 22.96 | 22.22 | 21.38 | 22.19 ± 0.65 | 基线 |
| distance | 20.00 | 19.68 | 19.98 | 19.89 ± 0.15 | -10.37% |
| distance_step | 21.64 | 21.32 | 20.98 | 21.31 ± 0.27 | -3.94% |

当前设置下，两个塑形方案在三个配对 seed 上都未超过 sparse。
distance_step 的 Return 216.16 和最高分 43 高于 sparse 的 211.87 和 35，但平均 Score 更低，
说明不能按不同定义的 Return 或单局最高分选择奖励。此现象本身不等于检测到奖励作弊。

行为复放：每组 150 局，自撞分别 130/126/130，撞墙 20/24/20；
超时、完整状态循环、零食物超时均为 0；全组最长连续未进食分别 42/42/44 步。
这只是本批开局下的观察，不能证明普遍不存在绕圈或把自撞原因全部归于某个奖励项。

后续 D-04 已完成探索实验，D-06 已补齐状态 x 奖励交互消融，见 [STATE_REWARD_ABLATION.md](STATE_REWARD_ABLATION.md)；不因负结果临时改系数、删 seed。
全量回归 270 passed，预算、有限 loss、奖励分项、同组配置与评估种子均已核对。

- [正式数据 JSON](../results/reward_experiments/reward_v2_20261018_152348_243907_d0be64a1/comparison.json)。
- [正式评估图](../results/reward_experiments/reward_v2_20261018_152348_243907_d0be64a1/figures/evaluation_scores.png)。
- [行为摘要](../results/reward_experiments/reward_v2_20261018_152348_243907_d0be64a1/behavior/analysis_20261018_153547_deb51a8a/summary.json)。
- [失败局面图](../results/reward_experiments/reward_v2_20261018_152348_243907_d0be64a1/behavior/analysis_20261018_153547_deb51a8a/examples.png)。

完整分项表、限制和 PPT 讲稿见 [D 工作汇总第 11 节](D_WORK_SUMMARY.md)。
