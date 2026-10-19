"""Controlled epsilon comparisons, schedule semantics and experiment integrity."""

import csv
import json

import numpy as np
import pytest

from algorithms.dqn import DQNAgent
from common.config import Config
from experiments.hyperparameter_experiment import run as experiment
from experiments.hyperparameter_experiment.plot import plot_exploration_experiment


@pytest.mark.parametrize("decay", experiment.DEFAULT_DECAYS)
def test_floor_matches_completed_environment_steps(decay):
    agent = DQNAgent(20, 3, Config(state_mode="v2", epsilon_decay=decay, hidden_dim=8))
    step = experiment.floor_step(1, 0.05, decay)
    for _ in range(step - 1):
        agent.on_env_step()
    assert agent.epsilon > 0.05
    agent.on_env_step()
    assert agent.epsilon == 0.05 and agent.global_step == step
    before = agent.epsilon
    agent.on_env_step(training=False)
    assert agent.epsilon == before and agent.global_step == step


def test_schedule_edge_cases():
    assert experiment.floor_step(1, 0, 0.99) is None
    assert experiment.floor_step(1, 0.05, 1) is None
    assert experiment.floor_step(0.05, 0.05, 0.99) == 0


def test_grid_changes_only_decay_and_seed_and_generates_all_plots(tmp_path):
    path = experiment.run_exploration_experiment(
        config=Config(state_mode="v2", hidden_dim=16, max_steps_per_episode=8,
                      min_buffer_size=4, batch_size=4, buffer_size=32),
        epsilon_decays=(0.99, 0.995, 0.999, 0.9995), seeds=(42, 43), total_steps=16,
        num_episodes=2, output_dir=tmp_path,
    )
    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["status"] == "completed" and len(result["training_runs"]) == 8
    configs = []
    for run in result["training_runs"]:
        directory = path.parent / run["run_dir"]
        config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
        decay = config.pop("epsilon_decay")
        assert decay == run["epsilon_decay"]
        assert config.pop("seed") == run["seed"]
        configs.append(config)
        assert run["global_step"] == 16 and run["update_count"] == 13
        assert run["final_epsilon"] == pytest.approx(max(0.05, decay ** 16))
        with (directory / "metrics.csv").open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                assert float(row["epsilon"]) == pytest.approx(max(0.05, decay ** int(row["global_step"])))
    assert all(config == configs[0] for config in configs)
    for label, directory in result["evaluation_dirs"].items():
        summary = json.loads((path.parent / directory / "summary.json").read_text(encoding="utf-8"))
        assert summary["protocol"]["evaluation_seeds"] == [10000, 10001]
        means = [model["mean_score"] for model in summary["models"]]
        assert result["explorations"][label]["mean_score"] == pytest.approx(np.mean(means))
    assert all(p.stat().st_size > 5000 for p in plot_exploration_experiment(path, bin_steps=4))


@pytest.mark.parametrize("arguments", [
    {"epsilon_decays": ()}, {"epsilon_decays": (0.99, 0.99)},
    {"epsilon_decays": (float("nan"),)}, {"epsilon_decays": (float("inf"),)},
    {"epsilon_decays": (0,)}, {"epsilon_decays": (1.1,)},
    {"seeds": ()}, {"seeds": (42, 42)}, {"seeds": (-1,)},
    {"config": Config(state_mode="v1")}, {"config": Config(state_mode="v2", reward_mode="distance")},
    {"total_steps": 0}, {"jobs": 0}, {"eval_seed": -1}, {"official": True, "seeds": (42,)},
])
def test_invalid_grid_fails_before_outputs(tmp_path, arguments):
    output = tmp_path / "output"
    with pytest.raises(ValueError):
        experiment.run_exploration_experiment(output_dir=output, **arguments)
    assert not output.exists()


def test_parallel_training_is_reproducible_and_failures_are_not_completed(tmp_path, monkeypatch):
    arguments = dict(config=Config(state_mode="v2", hidden_dim=8, max_steps_per_episode=5,
                                  min_buffer_size=4, batch_size=4, buffer_size=16),
                     seeds=(42, 43), epsilon_decays=(0.99,), total_steps=8,
                     num_episodes=1, output_dir=tmp_path)
    paths = [experiment.run_exploration_experiment(**arguments, jobs=jobs) for jobs in (1, 2)]
    results = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    assert results[0]["explorations"] == results[1]["explorations"]
    for index in range(2):
        metrics = []
        for path, result in zip(paths, results):
            directory = path.parent / result["training_runs"][index]["run_dir"]
            with (directory / "metrics.csv").open(encoding="utf-8", newline="") as stream:
                metrics.append([{key: value for key, value in row.items()
                                 if key not in ("run_id", "wall_clock_time")} for row in csv.DictReader(stream)])
        assert metrics[0] == metrics[1]

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(experiment, "train", interrupt)
    with pytest.raises(KeyboardInterrupt):
        experiment.run_exploration_experiment(**arguments)
    manifests = [json.loads(path.read_text(encoding="utf-8")) for path in tmp_path.glob("*/comparison.json")]
    assert sorted(item["status"] for item in manifests) == ["completed", "completed", "interrupted"]
