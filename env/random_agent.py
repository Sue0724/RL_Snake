"""随机策略，用作基线。

``select_action`` 的签名与 ``docs/INTERFACE.md`` §12 的 Agent API 一致，
所以 ``play.py`` / ``evaluate.py`` 不必修改调用代码就能把它换成 DQN。

没有 ``save`` / ``load``：随机策略没有需要持久化的状态。
"""
import numpy as np


class RandomAgent:
    """在 ``n_actions`` 个动作上均匀随机选择。"""

    def __init__(self, n_actions, seed=None):
        self.n_actions = n_actions
        self.np_random = np.random.default_rng(seed)

    def select_action(self, state, training=True):
        """均匀随机返回一个动作，``state`` 与 ``training`` 都不参与决策。"""
        return int(self.np_random.integers(self.n_actions))
