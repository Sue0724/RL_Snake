"""Double DQN 的目标计算必须由 Online 选动作、Target 评估。"""

import dataclasses

import numpy as np
import torch

from algorithms.double_dqn import DoubleDQNAgent
from common.config import Config


def make_agent(**overrides):
    config = dataclasses.replace(Config(hidden_dim=16), **overrides)
    return DoubleDQNAgent(11, 3, config)


def make_batch(size=3):
    return {
        "states": np.zeros((size, 11), dtype=np.float32),
        "actions": np.zeros(size, dtype=np.int64),
        "rewards": np.ones(size, dtype=np.float32),
        "next_states": np.zeros((size, 11), dtype=np.float32),
        "terminated": np.zeros(size, dtype=np.bool_),
        "truncated": np.zeros(size, dtype=np.bool_),
    }


def set_q_values(network, values):
    with torch.no_grad():
        for parameter in network.parameters():
            parameter.zero_()
        network.layers[-1].bias.copy_(torch.tensor(values, dtype=torch.float32))


def test_target_uses_online_argmax_and_target_value():
    agent = make_agent(gamma=1.0)
    set_q_values(agent.online_net, [0.0, 3.0, 0.0])
    set_q_values(agent.target_net, [10.0, 2.0, 0.0])
    batch = make_batch()
    batch["rewards"][:] = [1.0, 2.0, 3.0]
    batch["terminated"][:] = [False, True, False]

    tensors = agent._batch_tensors(batch)
    targets = agent._bellman_targets(
        tensors["rewards"], tensors["next_states"], tensors["terminated"]
    )

    # Online 选 action 1，Target 评估为 2；真终止样本只保留即时奖励。
    torch.testing.assert_close(targets, torch.tensor([3.0, 2.0, 5.0]))
    assert not targets.requires_grad


def test_update_uses_double_dqn_semantics_and_shared_training_loop():
    agent = make_agent(gamma=1.0, learning_rate=0.01)
    set_q_values(agent.online_net, [0.0, 3.0, 0.0])
    set_q_values(agent.target_net, [10.0, 2.0, 0.0])
    batch = make_batch()
    batch["actions"][:] = 1
    batch["rewards"][:] = 0.0

    loss = agent.update(batch)

    assert np.isfinite(loss)
    assert agent.update_count == 1
    assert all(parameter.grad is None for parameter in agent.target_net.parameters())
