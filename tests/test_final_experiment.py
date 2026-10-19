"""Frozen candidate, explicit reuse and unseen final-test separation."""

import json

import pytest

from common.config import Config
from experiments.algorithm_experiment.run import run_algorithm_experiment
from experiments.algorithm_experiment import final
from experiments.algorithm_experiment.analyze import analyze_algorithm_experiment
from experiments.algorithm_experiment.final_plot import plot_final_experiment


@pytest.fixture
def source(tmp_path):
    return run_algorithm_experiment(algorithms=("dqn",), seeds=(42, 43, 44), total_steps=8,
        num_episodes=2, holdout_seed=20000, output_dir=tmp_path / "source",
        config=Config(state_mode="v2", hidden_dim=8, min_buffer_size=4, batch_size=4, buffer_size=16))


def test_five_seed_grid_reuses_three_and_audits_all(tmp_path, source):
    path = final.run_final_experiment(source, output_dir=tmp_path / "final", official=False)
    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["status"] == "completed" and result["source_unchanged_after_run"]
    assert [run["seed"] for run in result["training_runs"]] == [42, 43, 44, 45, 46]
    assert [run["reused"] for run in result["training_runs"]] == [True, True, True, False, False]
    assert len(list((path.parent / "logs").iterdir())) == 2
    config = json.loads((path.parent / "final_config.json").read_text(encoding="utf-8"))
    assert config["config"]["seed"] == 42
    audit = json.loads(analyze_algorithm_experiment(path).read_text(encoding="utf-8"))
    assert audit["evaluation_records"] == 24 and len(audit["training"]) == 5
    outputs = plot_final_experiment(path, bin_steps=4)
    assert len(outputs) == 4 and all(p.stat().st_size > 5000 for p in outputs)


@pytest.mark.parametrize("arguments", [{"test_seed": 10000}, {"test_seed": 20000},
                                     {"test_seed": -1}, {"jobs": 0}, {"official": True}])
def test_invalid_protocol_before_output(tmp_path, source, arguments):
    options = dict(output_dir=tmp_path / "final", official=False)
    options.update(arguments)
    with pytest.raises(ValueError):
        final.run_final_experiment(source, **options)
    assert not (tmp_path / "final").exists()


def test_interruption_is_recorded(tmp_path, source, monkeypatch):
    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt
    monkeypatch.setattr(final, "train", interrupt)
    with pytest.raises(KeyboardInterrupt):
        final.run_final_experiment(source, output_dir=tmp_path / "final", official=False, jobs=1)
    paths = list((tmp_path / "final").glob("*/algorithm_comparison.json"))
    assert json.loads(paths[0].read_text(encoding="utf-8"))["status"] == "interrupted"
