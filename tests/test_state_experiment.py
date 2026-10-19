"""State comparisons fix rewards and record model capacity and seed variance."""

import csv
import json
from pathlib import Path

import numpy as np
import pytest

from common.config import Config
from experiments.state_experiment import run as state_run
from experiments.state_experiment.plot import plot_state_experiment


def test_state_grid_changes_only_state_and_seed(tmp_path):
    path = state_run.run_state_experiment(
        config=Config(hidden_dim=16, max_steps_per_episode=8, min_buffer_size=4,
                      batch_size=4, buffer_size=32),
        seeds=(42, 43), total_steps=16, num_episodes=2, output_dir=tmp_path,
    )
    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["status"] == "completed"
    assert result["protocol"]["environment_revision"] == "tail_occupancy_fixed"
    assert len(result["training_runs"]) == 4
    configs = []
    for run in result["training_runs"]:
        directory = path.parent / run["run_dir"]
        assert not Path(run["checkpoint"]).is_absolute()
        config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
        assert config.pop("state_mode") == run["state_mode"]
        assert config.pop("seed") == run["seed"]
        assert config["reward_mode"] == "sparse" and config["epsilon_decay"] == 0.9999
        configs.append(config)
        summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
        assert summary["global_step"] == 16 and summary["update_count"] == 13
    assert all(config == configs[0] for config in configs)
    assert result["protocol"]["parameter_counts"] == {"v1": 515, "v2": 659}
    for mode, directory in result["evaluation_dirs"].items():
        summary = json.loads((path.parent / directory / "summary.json").read_text(encoding="utf-8"))
        assert summary["protocol"]["evaluation_seeds"] == [10000, 10001]
        means = [model["mean_score"] for model in summary["models"]]
        assert result["state_modes"][mode]["mean_score"] == pytest.approx(np.mean(means))
        assert result["state_modes"][mode]["std_of_model_mean_scores"] == pytest.approx(np.std(means))
    with (path.parent / "comparison.csv").open(encoding="utf-8", newline="") as stream:
        assert len(list(csv.DictReader(stream))) == 4
    assert all(p.stat().st_size > 5000 for p in plot_state_experiment(path, bin_steps=4))


@pytest.mark.parametrize("overrides", [
    {"state_modes": ()}, {"state_modes": ("v1", "v1")}, {"state_modes": ("bad",)},
    {"seeds": ()}, {"seeds": (42, 42)}, {"seeds": (-1,)}, {"seeds": (42.5,)},
    {"total_steps": 0}, {"num_episodes": 0}, {"eval_seed": -1},
    {"config": Config(reward_mode="distance")}, {"config": Config(algorithm="double_dqn")},
    {"official": True}, {"official": True, "seeds": (42, 43, 44), "experiment": "debug_state"},
])
def test_invalid_comparison_fails_before_outputs(tmp_path, overrides):
    output = tmp_path / "output"
    with pytest.raises(ValueError):
        state_run.run_state_experiment(output_dir=output, **overrides)
    assert not output.exists()


@pytest.mark.parametrize("error, expected_status", [(KeyboardInterrupt(), "interrupted"),
                                                   (RuntimeError("test failure"), "failed")])
def test_errors_leave_accurate_manifest(tmp_path, monkeypatch, error, expected_status):
    def reject_training(*args, **kwargs):
        raise error

    monkeypatch.setattr(state_run, "train", reject_training)
    with pytest.raises(type(error)):
        state_run.run_state_experiment(seeds=(42,), total_steps=1, output_dir=tmp_path)
    path = next(tmp_path.glob("*/comparison.json"))
    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["status"] == expected_status
    with pytest.raises(ValueError, match="completed"):
        plot_state_experiment(path)
