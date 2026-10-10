"""Dueling DQN：使用 Value / Advantage 双流网络，训练目标与 DQN 相同。"""

from algorithms.dqn import DQNAgent
from algorithms.networks import DuelingQNetwork


class DuelingDQNAgent(DQNAgent):
    """复用 DQN 的更新逻辑，只替换共享特征与双流网络结构。"""

    network_class = DuelingQNetwork
