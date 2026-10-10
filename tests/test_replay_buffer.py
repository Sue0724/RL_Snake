"""回放池的数据完整性、随机采样及环境 -> 网络的集成检查。"""

import numpy as np
import pytest
import torch

from algorithms.networks import QNetwork
from common.config import Config
from common.replay_buffer import ReplayBuffer
from env.random_agent import RandomAgent
from env.snake_env import SnakeEnv


def populated_buffer(capacity=10, count=10, state_dim=11, seed=42):
    buffer = ReplayBuffer(capacity, seed=seed)
    for index in range(count):
        state = np.full(state_dim, index, dtype=np.float32)
        buffer.add(state, index % 3, index * 10.0, state + 1,
                   index % 3 == 0, index % 3 == 1)
    return buffer


@pytest.mark.parametrize("state_dim", [11, 20])
def test_sample_shapes_and_dtypes(state_dim):
    batch = populated_buffer(state_dim=state_dim).sample(4)
    assert set(batch) == {
        "states", "actions", "rewards", "next_states", "terminated", "truncated",
    }
    for field in ("states", "next_states"):
        assert batch[field].shape == (4, state_dim)
        assert batch[field].dtype == np.float32
    for field in ("actions", "rewards", "terminated", "truncated"):
        assert batch[field].shape == (4,)
    assert batch["actions"].dtype == np.int64
    assert batch["rewards"].dtype == np.float32
    assert batch["terminated"].dtype == np.bool_
    assert batch["truncated"].dtype == np.bool_


def test_random_sampling_keeps_all_six_fields_aligned():
    batch = populated_buffer().sample(10)
    for row, state in enumerate(batch["states"]):
        index = int(state[0])
        assert batch["actions"][row] == index % 3
        assert batch["rewards"][row] == index * 10.0
        np.testing.assert_array_equal(batch["next_states"][row], state + 1)
        assert bool(batch["terminated"][row]) == (index % 3 == 0)
        assert bool(batch["truncated"][row]) == (index % 3 == 1)


def test_capacity_overwrites_oldest_records():
    buffer = populated_buffer(capacity=3, count=8)
    assert len(buffer) == 3
    assert set(buffer.sample(3)["states"][:, 0]) == {5, 6, 7}


def test_sampling_is_without_replacement():
    batch = populated_buffer().sample(8)
    assert len(np.unique(batch["states"][:, 0])) == 8


def test_seed_reproduces_sampling_independently_of_global_rng():
    first = populated_buffer(seed=7)
    np.random.seed(123)
    np.random.random(100)
    second = populated_buffer(seed=7)
    for _ in range(3):
        batch_a, batch_b = first.sample(4), second.sample(4)
        for field in batch_a:
            np.testing.assert_array_equal(batch_a[field], batch_b[field])


def test_stored_states_and_sampled_batches_are_independent_copies():
    buffer = ReplayBuffer(2)
    state, next_state = np.zeros(11), np.ones(11)
    buffer.add(state, 0, 10, next_state, False, True)
    state[:] = 99
    next_state[:] = 99
    batch = buffer.sample(1)
    np.testing.assert_array_equal(batch["states"], np.zeros((1, 11)))
    np.testing.assert_array_equal(batch["next_states"], np.ones((1, 11)))
    batch["states"][:] = 99
    batch["next_states"][:] = 99
    again = buffer.sample(1)
    np.testing.assert_array_equal(again["states"], np.zeros((1, 11)))
    np.testing.assert_array_equal(again["next_states"], np.ones((1, 11)))


@pytest.mark.parametrize("capacity", [0, -1, 2.5])
def test_invalid_capacity_is_rejected(capacity):
    with pytest.raises(ValueError):
        ReplayBuffer(capacity)


@pytest.mark.parametrize("batch_size", [0, -1, 3, 1.5])
def test_invalid_or_oversized_batch_is_rejected(batch_size):
    with pytest.raises(ValueError):
        populated_buffer(count=2).sample(batch_size)


def test_empty_buffer_cannot_sample():
    with pytest.raises(ValueError):
        ReplayBuffer(10).sample(1)


@pytest.mark.parametrize("state,next_state", [([], []), ([1, 2], [1]), ([[1, 2]], [[1, 2]])])
def test_invalid_state_shapes_are_rejected_without_adding_data(state, next_state):
    buffer = ReplayBuffer(10)
    with pytest.raises(ValueError):
        buffer.add(state, 0, 0, next_state, False, False)
    assert len(buffer) == 0


def test_state_dimension_cannot_change_within_a_buffer():
    buffer = populated_buffer(count=1)
    with pytest.raises(ValueError):
        buffer.add(np.zeros(20), 0, 0, np.zeros(20), False, False)
    assert len(buffer) == 1


@pytest.mark.parametrize("action", [-1, 0.5])
def test_invalid_action_is_rejected(action):
    buffer = ReplayBuffer(10)
    with pytest.raises(ValueError):
        buffer.add(np.zeros(11), action, 0, np.zeros(11), False, False)
    assert len(buffer) == 0


def test_environment_buffer_network_pipeline():
    cfg = Config(hidden_dim=16, buffer_size=100, batch_size=16)
    env = SnakeEnv(cfg)
    buffer = ReplayBuffer(cfg.buffer_size, seed=cfg.seed)
    agent = RandomAgent(env.n_actions, seed=cfg.seed)
    state, _ = env.reset(seed=cfg.seed)
    try:
        for _ in range(100):
            action = agent.select_action(state)
            next_state, reward, terminated, truncated, _ = env.step(action)
            buffer.add(state, action, reward, next_state, terminated, truncated)
            state = next_state
            if terminated or truncated:
                state, _ = env.reset()

        batch = buffer.sample(cfg.batch_size)
        net = QNetwork(env.state_dim, env.n_actions, cfg.hidden_dim)
        q_values = net(torch.from_numpy(batch["states"]))
        chosen = q_values.gather(1, torch.from_numpy(batch["actions"])[:, None])
        assert q_values.shape == (cfg.batch_size, env.n_actions)
        assert chosen.shape == (cfg.batch_size, 1)
        assert torch.isfinite(chosen).all()
    finally:
        env.close()
