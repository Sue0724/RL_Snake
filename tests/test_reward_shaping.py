"""Reward semantics, unchanged dynamics and reward accounting."""

from collections import deque
import csv
import dataclasses
import json

import numpy as np
import pytest
import torch

from algorithms.factory import create_agent, load_agent
from common.config import Config, parse_args
from common.metrics import REWARD_FIELDS
from env.snake_env import LEFT, STRAIGHT, REWARD_MODES, SnakeEnv
from evaluate import evaluate
from train import train


def position(mode, *, food=(5, 8), head=(5, 5), **overrides):
    env = SnakeEnv(Config(reward_mode=mode, **overrides))
    env.reset(seed=42)
    env.body = deque([head, (head[0], head[1] - 1), (head[0], head[1] - 2)])
    env.occupied = set(env.body)
    env.direction = "right"
    env.food = food
    return env


@pytest.mark.parametrize("mode", REWARD_MODES)
def test_reset_has_zero_reward_components_even_after_a_step(mode):
    env = position(mode)
    env.step(STRAIGHT)
    _, info = env.reset(seed=42)
    assert all(info[name] == 0 for name in REWARD_FIELDS)


@pytest.mark.parametrize("mode, expected_step", [("sparse", 0), ("distance", 0), ("distance_step", -0.01)])
@pytest.mark.parametrize("action, delta", [(STRAIGHT, 1), (LEFT, -1)])
def test_toward_and_away_rewards(mode, expected_step, action, delta):
    env = position(mode)
    _, reward, terminated, truncated, info = env.step(action)
    distance = 0 if mode == "sparse" else 0.1 * delta
    assert info["distance_reward"] == pytest.approx(distance)
    assert info["step_reward"] == expected_step
    assert reward == pytest.approx(distance + expected_step)
    assert not terminated and not truncated


@pytest.mark.parametrize("mode", REWARD_MODES)
def test_eating_uses_old_food_not_respawned_food(mode, monkeypatch):
    env = position(mode, food=(5, 6))
    monkeypatch.setattr(env, "_spawn_food", lambda: setattr(env, "food", (0, 0)))
    _, reward, terminated, _, info = env.step(STRAIGHT)
    assert env.food == (0, 0)
    assert info["score"] == 1 and len(env.body) == 4
    assert info["food_reward"] == 10
    assert info["distance_reward"] == (0 if mode == "sparse" else 0.1)
    assert reward == pytest.approx(10 + sum(info[name] for name in REWARD_FIELDS[1:]))
    assert not terminated


@pytest.mark.parametrize("mode", REWARD_MODES)
def test_collision_has_no_distance_bonus_and_counts_the_last_step(mode):
    env = position(mode, head=(5, 9), food=(0, 0), max_steps_per_episode=1)
    _, reward, terminated, truncated, info = env.step(STRAIGHT)
    assert terminated and not truncated
    assert info["distance_reward"] == 0
    assert info["death_penalty"] == -10
    assert info["step_reward"] == (-0.01 if mode == "distance_step" else 0)
    assert reward == pytest.approx(-10 + info["step_reward"])


def test_self_collision_and_truncation_keep_distinct_reward_rules():
    env = position("distance_step")
    env.body = deque([(1, 1), (1, 2), (2, 2), (2, 1)])
    env.occupied = set(env.body)
    _, reward, terminated, truncated, info = env.step(STRAIGHT)
    assert terminated and not truncated and reward == pytest.approx(-10.01)
    assert info["distance_reward"] == 0
    env = position("distance_step", max_steps_per_episode=1)
    _, reward, terminated, truncated, info = env.step(STRAIGHT)
    assert not terminated and truncated and reward == pytest.approx(0.09)
    assert info["death_penalty"] == 0


def test_full_board_win_keeps_food_bonus_without_death_penalty():
    env = position("distance_step", board_size=2, initial_length=1, head=(1, 1))
    env.body = deque([(0, 0), (1, 0), (1, 1)])
    env.occupied = set(env.body)
    env.food = (0, 1)
    _, reward, terminated, truncated, info = env.step(STRAIGHT)
    assert terminated and not truncated
    assert reward == pytest.approx(10.09)
    assert info["death_penalty"] == 0 and info["score"] == 1


def test_closed_loop_cannot_collect_positive_undiscounted_distance_reward():
    env = position("distance_step", food=(0, 0))
    total_distance = total_step = 0.0
    start = env.body[0]
    for _ in range(4):
        _, _, terminated, truncated, info = env.step(LEFT)
        assert not terminated and not truncated
        total_distance += info["distance_reward"]
        total_step += info["step_reward"]
    assert env.body[0] == start and env.score == 0
    assert total_distance == pytest.approx(0)
    assert total_step == pytest.approx(-0.04)


@pytest.mark.parametrize("name", ["distance_reward_scale", "step_penalty"])
@pytest.mark.parametrize("value", [-0.1, 10, float("nan"), float("inf")])
def test_invalid_coefficients_fail(name, value):
    with pytest.raises(ValueError):
        SnakeEnv(Config(**{name: value}))


def test_combined_shaping_is_bounded_and_config_overrides_are_serializable():
    with pytest.raises(ValueError):
        SnakeEnv(Config(distance_reward_scale=6, step_penalty=4))
    cfg = parse_args(["--reward_mode", "distance_step", "--distance_reward_scale", "0.2",
                      "--step_penalty", "0.03"])
    _, reward, _, _, _ = position(**{
        "mode": cfg.reward_mode, "distance_reward_scale": cfg.distance_reward_scale,
        "step_penalty": cfg.step_penalty,
    }).step(STRAIGHT)
    assert reward == pytest.approx(0.17)
    assert json.loads(json.dumps(dataclasses.asdict(cfg)))["step_penalty"] == 0.03


def test_modes_change_only_reward_not_dynamics_or_rng():
    envs = [SnakeEnv(Config(reward_mode=mode)) for mode in REWARD_MODES]
    rng = np.random.default_rng(3)
    for episode in range(5):
        states = [env.reset(seed=episode)[0] for env in envs]
        while True:
            assert all(np.array_equal(states[0], state) for state in states)
            action = int(rng.integers(3))
            results = [env.step(action) for env in envs]
            assert all(list(env.body) == list(envs[0].body) and env.food == envs[0].food for env in envs)
            assert all(result[2:4] == results[0][2:4] for result in results)
            for _, reward, _, _, info in results:
                assert reward == pytest.approx(sum(info[name] for name in REWARD_FIELDS))
            states = [result[0] for result in results]
            if results[0][2] or results[0][3]:
                break


@pytest.mark.parametrize("mode", REWARD_MODES)
def test_training_evaluation_and_checkpoint_accounting(tmp_path, mode):
    config = Config(reward_mode=mode, max_steps_per_episode=3, initial_head=(5, 5),
                    hidden_dim=16, batch_size=4, min_buffer_size=4, buffer_size=32)
    run, status = train(config, total_steps=7, output_dir=tmp_path / "train")
    assert status == "completed"
    with (run / "metrics.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows[-1]["episode_complete"] == "False"
    assert sum(int(row["episode_length"]) for row in rows) == 7
    for row in rows:
        assert float(row["episode_return"]) == pytest.approx(sum(float(row[name]) for name in REWARD_FIELDS))
        if mode == "distance_step":
            assert float(row["step_reward"]) == pytest.approx(-0.01 * int(row["episode_length"]))
    model_path = run / "checkpoint.pt"
    source = model_path.read_bytes()
    restored, runtime = load_agent(model_path)
    assert runtime.reward_mode == mode and restored.config.distance_reward_scale == 0.1
    result = evaluate([model_path], num_episodes=3, output_dir=tmp_path / "evaluate")
    summary = json.loads((result / "summary.json").read_text(encoding="utf-8"))
    model = summary["models"][0]
    assert model["mean_return"] == pytest.approx(sum(model["mean_reward_components"].values()))
    with (result / "metrics.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            assert float(row["episode_return"]) == pytest.approx(sum(float(row[name]) for name in REWARD_FIELDS))
    assert model_path.read_bytes() == source


def test_old_checkpoint_without_new_config_fields_still_loads(tmp_path):
    path = tmp_path / "legacy.pt"
    create_agent(11, 3, Config(hidden_dim=16)).save(path)
    payload = torch.load(path, weights_only=True)
    del payload["config"]["distance_reward_scale"], payload["config"]["step_penalty"]
    torch.save(payload, path)
    _, config = load_agent(path)
    assert config.reward_mode == "sparse" and config.step_penalty == 0.01


def test_evaluation_rejects_different_shaping_coefficients_before_outputs(tmp_path):
    paths = []
    for index, scale in enumerate((0.1, 0.2)):
        path = tmp_path / f"model{index}.pt"
        create_agent(11, 3, Config(reward_mode="distance", distance_reward_scale=scale)).save(path)
        paths.append(path)
    with pytest.raises(ValueError, match="配置必须一致"):
        evaluate(paths, output_dir=tmp_path / "evaluations")
    assert not (tmp_path / "evaluations").exists()
