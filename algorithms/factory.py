"""公共 Agent 创建与模型加载；后续算法在这里注册。"""

import dataclasses
from pathlib import Path

from algorithms.dqn import DQNAgent
from algorithms.double_dqn import DoubleDQNAgent
from algorithms.dueling_dqn import DuelingDQNAgent
from common.checkpoint import CheckpointError, RESTORE_ERRORS, checkpoint_error, read_checkpoint
from common.config import Config
from env.random_agent import RandomAgent
from env.snake_env import SnakeEnv


# 只注册已经实现的算法，不把未实现算法映射为 DQN。
AGENT_CLASSES = {
    "dqn": DQNAgent,
    "double_dqn": DoubleDQNAgent,
    "dueling_dqn": DuelingDQNAgent,
    "random": RandomAgent,
}


def validate_agent_config(config: Config, *, training=False):
    """检查算法及其配置；Random 只用于评估和演示。"""
    if config.algorithm not in AGENT_CLASSES:
        supported = ", ".join(AGENT_CLASSES)
        raise ValueError(
            f"algorithm={config.algorithm!r} 尚未支持；当前可用：{supported}"
        )
    if config.algorithm == "random":
        if training:
            raise ValueError("Random 仅用于评估/演示，不支持训练或 checkpoint")
    else:
        AGENT_CLASSES[config.algorithm]._validate_config(config)


def create_agent(state_dim: int, n_actions: int, config: Config, *, training=False):
    """按 config.algorithm 创建 Agent；维度必须来自环境。"""
    validate_agent_config(config, training=training)
    agent_class = AGENT_CLASSES[config.algorithm]
    if config.algorithm == "random":
        return agent_class(n_actions, seed=config.seed)
    return agent_class(state_dim, n_actions, config)


def load_agent(path, *, device="cpu", render_mode=None):
    """恢复模型，返回 (agent, runtime_config)，用于评估或演示。

    环境、网络和训练参数取自 checkpoint，仅覆盖设备与渲染模式。
    agent.config 保留恢复的训练配置（设备除外）；返回的独立配置用于环境。
    调用方仍须 select_action(..., training=False) 才会关闭探索。
    不恢复环境/回放池，也不写入来源文件。
    """
    path = Path(path).expanduser().resolve()
    saved = read_checkpoint(path)
    try:
        try:
            config = Config(**saved["config"])
        except (KeyError, TypeError) as error:
            raise ValueError("checkpoint 缺少有效的 Config 配置") from error
        validate_agent_config(config, training=True)
        config.device = device
        config.render_mode = render_mode

        # 无渲染探测环境维度；恢复已有数据，整个流程只读取一次文件。
        env = SnakeEnv(dataclasses.replace(config, render_mode=None))
        try:
            if (saved.get("state_dim") != env.state_dim
                    or saved.get("n_actions") != env.n_actions):
                raise ValueError("checkpoint 网络维度与保存的环境配置不匹配")
            agent = create_agent(env.state_dim, env.n_actions, config)
            agent.restore_checkpoint(saved)
            agent.online_net.eval()
        finally:
            env.close()
    except CheckpointError:
        raise
    except RESTORE_ERRORS as error:
        raise checkpoint_error(path, error) from error
    return agent, config
