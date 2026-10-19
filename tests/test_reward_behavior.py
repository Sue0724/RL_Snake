"""Behavior diagnoses use full physical states rather than aliased observations."""

from collections import deque
import csv
import json

import pytest

from common.config import Config
from experiments.reward_experiment import behavior
from experiments.reward_experiment.run import run_reward_experiment


class FixedAgent:
    def __init__(self, action):
        self.action = action

    def select_action(self, state, training=False):
        assert training is False
        return self.action


def test_full_state_cycle_is_reported_as_timeout_not_food_progress(monkeypatch):
    real_env = behavior.SnakeEnv

    def make_env(config):
        env = real_env(config)
        reset = env.reset

        def fixed_reset(seed=None):
            reset(seed=seed)
            env.body = deque([(5, 5), (5, 4), (5, 3)])
            env.occupied = set(env.body)
            env.food = (0, 0)
            return env._get_state(), {}

        env.reset = fixed_reset
        return env

    monkeypatch.setattr(behavior, "SnakeEnv", make_env)
    row, trace = behavior.trace_episode(FixedAgent(1), Config(max_steps_per_episode=20), 42)
    assert row["outcome"] == "timeout" and row["score"] == 0
    assert row["cycle_detected"] and row["cycle_period"] == 4
    assert row["max_steps_without_food"] == 20 and len(trace) == 20


def test_wall_death_is_not_mislabeled_as_cycle():
    row, _ = behavior.trace_episode(FixedAgent(0), Config(initial_head=(5, 5)), 42)
    assert row["outcome"] == "wall" and not row["cycle_detected"]
    assert row["episode_length"] == 5 and row["death_penalty"] == -10


def test_behavior_replays_original_records_and_rejects_mismatches(tmp_path):
    comparison_path = run_reward_experiment(
        config=Config(hidden_dim=16, max_steps_per_episode=8, min_buffer_size=4,
                      batch_size=4, buffer_size=32), reward_modes=("sparse", "distance_step"),
        seeds=(42,), total_steps=8, num_episodes=2, output_dir=tmp_path,
    )
    result_path = behavior.analyze_behavior(comparison_path)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["status"] == "completed" and len(result["source_checkpoint_sha256"]) == 2
    assert (result_path.parent / "examples.png").stat().st_size > 5000
    assert all(group["episodes"] == 2 for group in result["reward_modes"].values())
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    metric_path = comparison_path.parent / comparison["evaluation_dirs"]["sparse"] / "metrics.csv"
    with metric_path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        rows = list(reader)
    rows[0]["score"] = str(int(rows[0]["score"]) + 1)
    with metric_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(RuntimeError, match="Replay mismatch"):
        behavior.analyze_behavior(comparison_path)
    assert json.loads(result_path.read_text(encoding="utf-8"))["status"] == "completed"
