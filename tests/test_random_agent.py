"""RandomAgent 契约测试：``select_action`` 对齐 ``docs/INTERFACE.md`` §12。"""
import numpy as np

from env.random_agent import RandomAgent


def test_action_stays_in_range():
    agent = RandomAgent(3, seed=0)
    state = np.zeros(11, dtype=np.float32)

    assert {agent.select_action(state) for _ in range(500)} == {0, 1, 2}


def test_same_seed_gives_same_actions():
    first, second = RandomAgent(3, seed=7), RandomAgent(3, seed=7)

    assert [first.select_action(None) for _ in range(20)] == \
           [second.select_action(None) for _ in range(20)]


def test_training_flag_does_not_change_behaviour():
    """随机策略没有探索与评估之分，``training`` 取值不影响结果。"""
    first, second = RandomAgent(3, seed=7), RandomAgent(3, seed=7)

    assert [first.select_action(None, training=True) for _ in range(20)] == \
           [second.select_action(None, training=False) for _ in range(20)]
