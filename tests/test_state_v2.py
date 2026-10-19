"""V2 geometry, observation consistency, tail occupancy and checkpoint integration."""

from collections import deque
import hashlib
import json

import numpy as np
import pytest

from algorithms.factory import load_agent
from common.config import Config
from env.snake_env import RIGHT, STRAIGHT, SnakeEnv
from evaluate import evaluate
from train import train


def place(env, body, direction="right", food=(0, 0)):
    env.body, env.occupied = deque(body), set(body)
    env.direction, env.food, env.steps, env.done = direction, food, 0, False


@pytest.mark.parametrize("mode, dimension", [("v1", 11), ("v2", 20)])
def test_state_shapes_dtypes_ranges_and_seed(mode, dimension):
    a, b = SnakeEnv(Config(state_mode=mode)), SnakeEnv(Config(state_mode=mode))
    for seed in (0, 42, 43):
        first, _ = a.reset(seed=seed)
        second, _ = b.reset(seed=seed)
        assert a.state_dim == dimension and first.shape == (dimension,)
        assert first.dtype == np.float32
        np.testing.assert_array_equal(first, second)
        assert np.all((first >= 0) & (first <= 1))


@pytest.mark.parametrize("size", [5, 10, 12])
def test_normalized_distance_extremes(size):
    env = SnakeEnv(Config(state_mode="v2", board_size=size))
    place(env, [(0, 0)], food=(size - 1, size - 1))
    assert env._get_state()[11] == 1
    env.food = (0, 1)
    assert env._get_state()[11] == pytest.approx(1 / (2 * (size - 1)))


@pytest.mark.parametrize("direction, cells", [
    ("up", [(4, 5), (4, 6), (5, 6), (6, 6), (6, 5), (6, 4), (5, 4), (4, 4)]),
    ("right", [(5, 6), (6, 6), (6, 5), (6, 4), (5, 4), (4, 4), (4, 5), (4, 6)]),
    ("down", [(6, 5), (6, 4), (5, 4), (4, 4), (4, 5), (4, 6), (5, 6), (6, 6)]),
    ("left", [(5, 4), (4, 4), (4, 5), (4, 6), (5, 6), (6, 6), (6, 5), (6, 4)]),
])
def test_ring_all_eight_cells_in_all_four_orientations(direction, cells):
    env = SnakeEnv(Config(state_mode="v2"))
    for index, cell in enumerate(cells):
        place(env, [(5, 5), cell, (8, 8)], direction)
        expected = np.zeros(8)
        expected[index] = 1
        np.testing.assert_array_equal(env._get_state()[12:], expected)
        # The same cell is free if it is the tail instead of a body segment.
        place(env, [(5, 5), (8, 8), cell], direction)
        np.testing.assert_array_equal(env._get_state()[12:], np.zeros(8))


def test_ring_out_of_bounds_is_occupied_and_matches_dangers():
    env = SnakeEnv(Config(state_mode="v2"))
    place(env, [(0, 0)], "up", food=(4, 4))
    state = env._get_state()
    np.testing.assert_array_equal(state[12:], [1, 1, 0, 0, 0, 1, 1, 1])
    np.testing.assert_array_equal(state[[12, 18, 14]], state[:3])


def test_eating_observes_new_food_consistently(monkeypatch):
    env = SnakeEnv(Config(state_mode="v2"))
    place(env, [(5, 5), (5, 4), (5, 3)], food=(5, 6))
    monkeypatch.setattr(env, "_spawn_food", lambda: setattr(env, "food", (0, 0)))
    state, reward, _, _, _ = env.step(STRAIGHT)
    assert reward == 10 and state[11] == pytest.approx(11 / 18)
    assert state[7] == state[9] == 1 and state[8] == state[10] == 0


def test_terminal_full_board_distance_is_zero():
    env = SnakeEnv(Config(state_mode="v2", board_size=2, initial_length=1))
    place(env, [(0, 0), (1, 0), (1, 1)], food=(0, 1))
    state, reward, terminated, truncated, _ = env.step(STRAIGHT)
    assert terminated and not truncated and reward == 10
    assert state[11] == 0 and env.occupied == set(env.body)


@pytest.mark.parametrize("mode", ["v1", "v2"])
def test_entering_tail_preserves_occupancy_and_future_collision_checks(mode):
    env = SnakeEnv(Config(state_mode=mode))
    place(env, [(1, 1), (2, 1), (2, 2), (1, 2)], food=(9, 9))
    for action in (STRAIGHT, RIGHT, RIGHT, RIGHT, RIGHT):
        _, _, terminated, truncated, _ = env.step(action)
        assert not terminated and not truncated
        assert env.occupied == set(env.body)
    # After a tail move, the old head remains a body segment and must block entry.
    assert env.body[1] in env.occupied


@pytest.mark.parametrize("reward_mode", ["sparse", "distance", "distance_step"])
def test_v2_preserves_v1_prefix_rewards_and_dynamics(reward_mode):
    v1 = SnakeEnv(Config(reward_mode=reward_mode))
    v2 = SnakeEnv(Config(state_mode="v2", reward_mode=reward_mode))
    rng = np.random.default_rng(7)
    for seed in range(5):
        s1, _ = v1.reset(seed=seed)
        s2, _ = v2.reset(seed=seed)
        for _ in range(100):
            np.testing.assert_array_equal(s1, s2[:11])
            np.testing.assert_array_equal(s2[[12, 18, 14]], s2[:3])
            action = int(rng.integers(3))
            s1, *r1 = v1.step(action)
            s2, *r2 = v2.step(action)
            assert r1 == r2
            assert list(v1.body) == list(v2.body) and v1.food == v2.food
            assert v2.occupied == set(v2.body)
            if r1[1] or r1[2]:
                break


@pytest.mark.parametrize("algorithm", ["dqn", "double_dqn", "dueling_dqn"])
def test_v2_trains_loads_and_evaluates_without_changing_checkpoint(tmp_path, algorithm):
    config = Config(state_mode="v2", algorithm=algorithm, hidden_dim=16,
                    min_buffer_size=4, batch_size=4, buffer_size=32, max_steps_per_episode=8)
    directory, status = train(config, total_steps=16, output_dir=tmp_path / "train")
    assert status == "completed"
    checkpoint = directory / "checkpoint.pt"
    before = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    agent, runtime = load_agent(checkpoint)
    assert agent.state_dim == 20 and runtime.state_mode == "v2"
    result = evaluate([checkpoint], num_episodes=2, output_dir=tmp_path / "evaluate")
    summary = json.loads((result / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "completed"
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == before
