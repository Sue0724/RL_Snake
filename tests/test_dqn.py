"""DQN 动作、Bellman 计算、更新时机和 checkpoint 的算法检查。"""

import copy
import dataclasses

import numpy as np
import pytest
import torch

from algorithms.dqn import DQNAgent
from common.config import Config
from common.replay_buffer import ReplayBuffer
from env.snake_env import SnakeEnv


def make_agent(state_dim=11, n_actions=3, **overrides):
    cfg = dataclasses.replace(Config(hidden_dim=16), **overrides)
    return DQNAgent(state_dim, n_actions, cfg)


def make_batch(size=3, state_dim=11):
    return {
        "states": np.zeros((size, state_dim), dtype=np.float32),
        "actions": np.zeros(size, dtype=np.int64),
        "rewards": np.ones(size, dtype=np.float32),
        "next_states": np.zeros((size, state_dim), dtype=np.float32),
        "terminated": np.zeros(size, dtype=np.bool_),
        "truncated": np.zeros(size, dtype=np.bool_),
    }


def set_constant_values(network, values):
    with torch.no_grad():
        for parameter in network.parameters():
            parameter.zero_()
        network.layers[-1].bias.copy_(torch.tensor(values, dtype=torch.float32))


def assert_same_network(first, second):
    for key, value in first.state_dict().items():
        torch.testing.assert_close(value, second.state_dict()[key], rtol=0, atol=0)


def test_initial_target_is_an_independent_frozen_copy():
    agent = make_agent()
    assert_same_network(agent.online_net, agent.target_net)
    assert not agent.target_net.training
    for online, target in zip(agent.online_net.parameters(), agent.target_net.parameters()):
        assert online.data_ptr() != target.data_ptr()
        assert online.requires_grad and not target.requires_grad


def test_initialization_and_exploration_are_reproducible_without_global_rng_changes():
    before = torch.random.get_rng_state().clone()
    first, second = make_agent(seed=7), make_agent(seed=7)
    assert torch.equal(before, torch.random.get_rng_state())
    assert_same_network(first.online_net, second.online_net)
    assert [first.select_action(np.zeros(11)) for _ in range(20)] == [
        second.select_action(np.zeros(11)) for _ in range(20)
    ]


def test_epsilon_one_explores_all_available_actions():
    agent = make_agent()
    assert {agent.select_action(np.zeros(11)) for _ in range(200)} == {0, 1, 2}
    assert agent.global_step == 0 and agent.epsilon == 1.0


@pytest.mark.parametrize("training", [True, False])
def test_zero_epsilon_chooses_largest_online_value(training):
    agent = make_agent(epsilon_start=0.0, epsilon_end=0.0)
    set_constant_values(agent.online_net, [-2.0, 5.0, 1.0])
    assert agent.select_action(np.zeros(11), training=training) == 1


def test_evaluation_is_greedy_and_preserves_exploration_state():
    agent = make_agent()
    set_constant_values(agent.online_net, [-2.0, 5.0, 1.0])
    rng_before = copy.deepcopy(agent._rng.bit_generator.state)
    for _ in range(10):
        assert agent.select_action(np.zeros(11), training=False) == 1
        agent.on_env_step(training=False)
    assert agent._rng.bit_generator.state == rng_before
    assert agent.epsilon == 1.0 and agent.global_step == 0 and agent.update_count == 0


def test_decay_only_counts_completed_training_steps_and_stops_at_floor():
    agent = make_agent(epsilon_start=1.0, epsilon_end=0.2, epsilon_decay=0.5)
    for expected in [0.5, 0.25, 0.2, 0.2]:
        agent.on_env_step()
        assert agent.epsilon == pytest.approx(expected)
    agent.update(None)
    assert agent.global_step == 4 and agent.update_count == 0


@pytest.mark.parametrize("state_dim,n_actions", [(11, 3), (20, 4)])
def test_agent_accepts_dynamic_dimensions(state_dim, n_actions):
    agent = make_agent(state_dim, n_actions)
    assert 0 <= agent.select_action(np.zeros(state_dim)) < n_actions
    assert np.isfinite(agent.update(make_batch(state_dim=state_dim)))


def test_bellman_values_use_target_network_and_bootstrap_after_truncation():
    agent = make_agent(gamma=0.9)
    set_constant_values(agent.online_net, [0.0, 0.0, 0.0])
    set_constant_values(agent.target_net, [-2.0, 5.0, 1.0])
    batch = make_batch()
    batch["rewards"][:] = [1.0, 2.0, 3.0]
    batch["terminated"][:] = [False, True, False]
    batch["truncated"][:] = [False, False, True]

    tensors = agent._batch_tensors(batch)
    targets = agent._bellman_targets(
        tensors["rewards"], tensors["next_states"], tensors["terminated"]
    )
    # 普通步 1+0.9*5；真终止只有 2；截断仍为 3+0.9*5。
    torch.testing.assert_close(targets, torch.tensor([5.5, 2.0, 7.5]))
    assert not targets.requires_grad
    # 当前预测为零，三个 Smooth L1 损失是 5、1.5、7，平均 4.5。
    assert agent.update(batch) == pytest.approx(4.5)
    assert all(parameter.grad is None for parameter in agent.target_net.parameters())


def test_update_uses_recorded_action_and_changes_online_parameters():
    agent = make_agent(gamma=0.0)
    set_constant_values(agent.online_net, [1.0, 2.0, 3.0])
    batch = make_batch()
    batch["actions"][:] = [0, 1, 2]
    batch["rewards"][:] = [0.0, 0.0, 0.0]
    before = [parameter.detach().clone() for parameter in agent.online_net.parameters()]
    assert agent.update(batch) == pytest.approx(1.5)
    assert any(not torch.equal(old, new) for old, new in zip(before, agent.online_net.parameters()))
    assert agent.update_count == 1
    assert agent.global_step == 0 and agent.epsilon == 1.0


def test_target_sync_counts_successful_gradient_updates():
    agent = make_agent(target_update_interval=2)
    before = {key: value.clone() for key, value in agent.target_net.state_dict().items()}
    for _ in range(5):
        agent.on_env_step()
    agent.update(make_batch())
    for key, value in before.items():
        torch.testing.assert_close(value, agent.target_net.state_dict()[key])
    agent.update(make_batch())
    assert_same_network(agent.online_net, agent.target_net)
    assert agent.update_count == 2 and agent.global_step == 5
    assert not agent.target_net.training


def test_warmup_none_does_not_update_network_or_counters():
    agent = make_agent()
    before = {key: value.clone() for key, value in agent.online_net.state_dict().items()}
    assert agent.update(None) is None
    for key, value in before.items():
        torch.testing.assert_close(value, agent.online_net.state_dict()[key])
    assert not agent.optimizer.state
    assert agent.update_count == 0 and agent.global_step == 0


def test_checkpoint_restores_networks_optimizer_schedule_rng_and_next_update(tmp_path):
    agent = make_agent(target_update_interval=2)
    batch = make_batch()
    agent.update(batch)
    for _ in range(3):
        agent.on_env_step()
    checkpoint = tmp_path / "nested" / "checkpoint.pt"
    agent.save(checkpoint)

    restored = make_agent(seed=13, learning_rate=0.02, gamma=0.5, epsilon_decay=0.5)
    restored.load(checkpoint)
    assert_same_network(agent.online_net, restored.online_net)
    assert_same_network(agent.target_net, restored.target_net)
    assert restored.config == agent.config
    assert restored.epsilon == agent.epsilon
    assert restored.global_step == 3 and restored.update_count == 1
    assert restored.optimizer.param_groups[0]["lr"] == agent.config.learning_rate
    assert [agent.select_action(np.zeros(11)) for _ in range(20)] == [
        restored.select_action(np.zeros(11)) for _ in range(20)
    ]
    assert restored.update(batch) == pytest.approx(agent.update(batch), rel=0, abs=0)
    assert_same_network(agent.online_net, restored.online_net)
    assert_same_network(agent.target_net, restored.target_net)
    assert restored.update_count == 2


@pytest.mark.parametrize("state_dim,n_actions,hidden_dim", [(20, 3, 16), (11, 4, 16), (11, 3, 8)])
def test_checkpoint_with_different_architecture_is_rejected(tmp_path, state_dim, n_actions, hidden_dim):
    checkpoint = tmp_path / "checkpoint.pt"
    make_agent().save(checkpoint)
    other = make_agent(state_dim, n_actions, hidden_dim=hidden_dim)
    with pytest.raises(ValueError, match="不匹配"):
        other.load(checkpoint)


@pytest.mark.parametrize("field,value", [
    ("gamma", 1.1), ("epsilon_end", 1.1), ("epsilon_decay", 0),
    ("learning_rate", 0), ("target_update_interval", 0),
])
def test_invalid_algorithm_config_is_rejected(field, value):
    with pytest.raises(ValueError):
        make_agent(**{field: value})


@pytest.mark.parametrize("field,value", [
    ("actions", np.array([0, 1, 3])),
    ("actions", np.array([0.0, 0.5, 1.0])),
    ("rewards", np.ones((3, 1))),
    ("terminated", np.zeros(3, dtype=np.float32)),
    ("next_states", np.zeros((3, 20))),
])
def test_invalid_batches_fail_before_an_update(field, value):
    agent = make_agent()
    batch = make_batch()
    batch[field] = value
    with pytest.raises(ValueError):
        agent.update(batch)
    assert agent.update_count == 0


def test_nonfinite_loss_is_rejected_before_optimizer_update():
    agent = make_agent()
    batch = make_batch()
    batch["rewards"][0] = np.nan
    with pytest.raises(FloatingPointError):
        agent.update(batch)
    assert agent.update_count == 0 and not agent.optimizer.state


def test_short_training_loop_connects_environment_replay_and_agent():
    cfg = Config(hidden_dim=16, batch_size=16, min_buffer_size=32,
                 buffer_size=200, target_update_interval=5, max_steps_per_episode=30)
    env = SnakeEnv(cfg)
    agent = DQNAgent(env.state_dim, env.n_actions, cfg)
    buffer = ReplayBuffer(cfg.buffer_size, seed=cfg.seed)
    state, _ = env.reset(seed=cfg.seed)
    losses = []
    try:
        for _ in range(160):
            action = agent.select_action(state)
            next_state, reward, terminated, truncated, _ = env.step(action)
            buffer.add(state, action, reward, next_state, terminated, truncated)
            agent.on_env_step()
            batch = buffer.sample(cfg.batch_size) if len(buffer) >= max(
                cfg.min_buffer_size, cfg.batch_size
            ) else None
            loss = agent.update(batch)
            if loss is not None:
                losses.append(loss)
            state = next_state
            if terminated or truncated:
                state, _ = env.reset()
        assert agent.global_step == 160 and agent.update_count == 129
        assert len(losses) == 129 and np.isfinite(losses).all()
        assert agent.epsilon == pytest.approx(cfg.epsilon_decay ** 160)
    finally:
        env.close()
