"""Reward comparison reproducibility, output integrity and plot regeneration."""

import csv
import json
from pathlib import Path

import numpy as np
import pytest

from common.config import Config
from experiments.reward_experiment import run as reward_run
from experiments.reward_experiment.plot import plot_reward_experiment, training_bins


def test_reward_grid_uses_fixed_configs_shared_evaluation_and_raw_logs(tmp_path):
    path = reward_run.run_reward_experiment(
        config=Config(hidden_dim=16, max_steps_per_episode=8, batch_size=4,
                      min_buffer_size=4, buffer_size=64),
        seeds=(42, 43), total_steps=32, num_episodes=3, output_dir=tmp_path,
    )
    comparison = json.loads(path.read_text(encoding="utf-8"))
    assert comparison["status"] == "completed"
    assert comparison["protocol"]["run_type"] == "debug"
    assert len(comparison["training_runs"]) == 6
    reference_configs = {}
    for run in comparison["training_runs"]:
        assert not Path(run["checkpoint"]).is_absolute()
        assert (path.parent / run["checkpoint"]).exists()
        directory = path.parent / run["run_dir"]
        config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
        mode, seed = config.pop("reward_mode"), config.pop("seed")
        assert mode == run["reward_mode"] and seed == run["seed"]
        reference_configs[(mode, seed)] = config
        summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
        assert summary["global_step"] == 32 and summary["update_count"] == 29
    assert all(config == next(iter(reference_configs.values())) for config in reference_configs.values())
    for mode, directory in comparison["evaluation_dirs"].items():
        summary = json.loads((path.parent / directory / "summary.json").read_text(encoding="utf-8"))
        assert summary["protocol"]["evaluation_seeds"] == [10000, 10001, 10002]
        means = [model["mean_score"] for model in summary["models"]]
        assert comparison["reward_modes"][mode]["mean_score"] == pytest.approx(np.mean(means))
        assert comparison["reward_modes"][mode]["std_of_model_mean_scores"] == pytest.approx(np.std(means))
    with (path.parent / "comparison.csv").open(encoding="utf-8", newline="") as stream:
        assert len(list(csv.DictReader(stream))) == 6
    figures = plot_reward_experiment(path, bin_steps=8)
    assert len(figures) == 2 and all(figure.stat().st_size > 5000 for figure in figures)


@pytest.mark.parametrize("overrides", [
    {"seeds": ()}, {"seeds": (42, 42)}, {"seeds": (-1,)},
    {"reward_modes": ()}, {"reward_modes": ("distance", "distance")},
    {"reward_modes": ("unknown",)}, {"total_steps": 0}, {"eval_seed": -1},
    {"config": Config(algorithm="double_dqn")},
    {"config": Config(distance_reward_scale=float("nan"))},
    {"config": Config(state_mode="unknown")},
    {"official": True},
    {"official": True, "seeds": (42, 43, 44), "experiment": "reward", "num_episodes": 1},
])
def test_invalid_grid_fails_before_creating_outputs(tmp_path, overrides):
    output = tmp_path / "output"
    arguments = {"output_dir": output, "seeds": (42,), "total_steps": 1, **overrides}
    with pytest.raises((ValueError, NotImplementedError)):
        reward_run.run_reward_experiment(**arguments)
    assert not output.exists()


def test_interrupted_training_is_not_reported_as_completed(tmp_path, monkeypatch):
    original_train = reward_run.train

    def interrupted(*args, **kwargs):
        directory, _ = original_train(*args, **kwargs)
        return directory, "interrupted"

    monkeypatch.setattr(reward_run, "train", interrupted)
    with pytest.raises(InterruptedError):
        reward_run.run_reward_experiment(seeds=(42,), total_steps=1, output_dir=tmp_path)
    path = next(tmp_path.glob("*/comparison.json"))
    comparison = json.loads(path.read_text(encoding="utf-8"))
    assert comparison["status"] == "interrupted"
    assert len(comparison["training_runs"]) == 1
    assert not comparison["evaluation_dirs"]
    with pytest.raises(ValueError, match="completed"):
        plot_reward_experiment(path)


def test_plot_bins_ignore_partial_episodes_and_do_not_interpolate(tmp_path):
    path = tmp_path / "metrics.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["global_step", "score", "episode_complete"])
        writer.writeheader()
        writer.writerows([
            {"global_step": 1, "score": 2, "episode_complete": True},
            {"global_step": 4, "score": 4, "episode_complete": True},
            {"global_step": 10, "score": 99, "episode_complete": False},
        ])
    values = training_bins(path, total_steps=10, bin_steps=5, metric="score")
    assert values[0] == 3 and np.isnan(values[1])


def test_parallel_and_serial_runs_produce_identical_metrics(tmp_path):
    arguments = dict(config=Config(hidden_dim=16, max_steps_per_episode=8,
                                  batch_size=4, min_buffer_size=4, buffer_size=32),
                     reward_modes=("sparse",), seeds=(42, 43), total_steps=16,
                     num_episodes=2, output_dir=tmp_path)
    paths = [reward_run.run_reward_experiment(**arguments, jobs=jobs) for jobs in (1, 2)]
    summaries = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    assert summaries[0]["reward_modes"] == summaries[1]["reward_modes"]
    for serial, parallel in zip(*[summary["training_runs"] for summary in summaries]):
        rows = []
        for path, run in zip(paths, (serial, parallel)):
            with (path.parent / run["run_dir"] / "metrics.csv").open(encoding="utf-8", newline="") as stream:
                rows.append([{key: value for key, value in row.items()
                              if key not in ("run_id", "wall_clock_time")} for row in csv.DictReader(stream)])
        assert rows[0] == rows[1]
