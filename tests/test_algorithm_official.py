"""Official algorithm protocol, parallel execution and holdout separation."""

import csv
import json

import pytest

from common.config import Config
from experiments.algorithm_experiment import run as experiment
from experiments.algorithm_experiment.plot import plot_algorithm_experiment
from experiments.algorithm_experiment.analyze import analyze_algorithm_experiment


@pytest.mark.parametrize("arguments", [
    {"algorithms": ()}, {"algorithms": ("dqn", "dqn")}, {"algorithms": ("invalid",)},
    {"seeds": ()}, {"seeds": (42, 42)}, {"seeds": (-1,)}, {"seeds": (True,)},
    {"total_steps": 0}, {"jobs": 0}, {"eval_seed": -1}, {"eval_seed": None},
    {"holdout_seed": 10020}, {"holdout_seed": -1}, {"official": True, "seeds": (42,)},
])
def test_invalid_protocol_before_outputs(tmp_path, arguments):
    with pytest.raises(ValueError):
        experiment.run_algorithm_experiment(output_dir=tmp_path / "new", **arguments)
    assert not (tmp_path / "new").exists()


def test_config_grid_holdout_parallel_and_plots(tmp_path):
    arguments = dict(config=Config(state_mode="v2", hidden_dim=8, max_steps_per_episode=5,
                                  min_buffer_size=2, batch_size=4, buffer_size=32),
                     seeds=(42, 43), total_steps=12, num_episodes=2, holdout_seed=20000,
                     output_dir=tmp_path, experiment="debug_algorithm")
    paths = [experiment.run_algorithm_experiment(**arguments, jobs=jobs) for jobs in (1, 2)]
    results = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    assert results[0]["algorithms"] == results[1]["algorithms"]
    assert results[0]["holdout_algorithms"] == results[1]["holdout_algorithms"]
    for path, result in zip(paths, results):
        assert len(result["training_runs"]) == 6
        configs = []
        for run in result["training_runs"]:
            config = json.loads((path.parent / run["run_dir"] / "config.json").read_text(encoding="utf-8"))
            assert config.pop("algorithm") == run["algorithm"]
            assert config.pop("seed") == run["seed"]
            configs.append(config)
            assert run["global_step"] == 12 and run["update_count"] == 9
        assert all(config == configs[0] for config in configs)
        assert result["selected_algorithm"] == max(result["protocol"]["algorithms"],
                                                  key=lambda name: result["algorithms"][name]["mean_score"])
        for key, first_seed in (("evaluation_dir", 10000), ("holdout_evaluation_dir", 20000)):
            evaluation = json.loads((path.parent / result[key] / "config.json").read_text(encoding="utf-8"))
            assert evaluation["protocol"]["evaluation_seeds"] == [first_seed, first_seed + 1]
            assert all(evaluation["protocol"][key] is False
                       for key in ("exploration", "network_update", "replay_write"))
    for first, second in zip(results[0]["training_runs"], results[1]["training_runs"]):
        data = []
        for run in (first, second):
            with (tmp_path / run["run_dir"] / "metrics.csv").open(encoding="utf-8", newline="") as stream:
                data.append([{k: v for k, v in row.items() if k not in ("run_id", "wall_clock_time")}
                             for row in csv.DictReader(stream)])
        assert data[0] == data[1]
    assert all(path.stat().st_size > 5000 for path in plot_algorithm_experiment(paths[0], bin_steps=4))
    audit_path = analyze_algorithm_experiment(paths[0])
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["status"] == "completed" and audit["evaluation_records"] == 28
    assert len(audit["training"]) == 6
    assert audit["selected_algorithm"] == results[0]["selected_algorithm"]
    assert all(len(run["sha256"]) == 64 for run in audit["training"])
    parameters = {run["algorithm"]: run["parameter_count"] for run in audit["training"]}
    assert parameters["dqn"] == parameters["double_dqn"]
    assert parameters["dueling_dqn"] - parameters["dqn"] == 9
    result = results[0]
    result["training_runs"][0]["global_step"] += 1
    paths[0].write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(ValueError, match="Training budget mismatch"):
        analyze_algorithm_experiment(paths[0])


@pytest.mark.parametrize("error, status", [(KeyboardInterrupt, "interrupted"), (RuntimeError, "failed")])
def test_failure_manifest(tmp_path, monkeypatch, error, status):
    def fail(*args, **kwargs):
        raise error("test interruption")
    monkeypatch.setattr(experiment, "train", fail)
    with pytest.raises(error):
        experiment.run_algorithm_experiment(output_dir=tmp_path)
    manifests = list(tmp_path.glob("*/algorithm_comparison.json"))
    assert len(manifests) == 1
    result = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert result["status"] == status and result["error"]


@pytest.mark.parametrize("target,field,value,message", [
    ("training", "epsilon", "0.123", "Epsilon schedule"),
    ("training", "loss", "nan", "Non-finite loss"),
    ("training", "food_reward", "12345", "Training reward accounting"),
    ("training", "global_step", "12345", "CSV cumulative steps"),
    ("evaluation", "evaluation_seed", "999", "Per-model evaluation seeds"),
    ("evaluation", "food_reward", "12345", "Evaluation reward accounting"),
    ("evaluation", "algorithm", "unknown", "Evaluation row identity"),
])
def test_audit_rejects_tampered_raw_data(tmp_path, target, field, value, message):
    path = experiment.run_algorithm_experiment(
        algorithms=("dqn",), seeds=(42,), total_steps=4, num_episodes=1,
        config=Config(hidden_dim=8), output_dir=tmp_path)
    result = json.loads(path.read_text(encoding="utf-8"))
    directory = (result["training_runs"][0]["run_dir"] if target == "training" else result["evaluation_dir"])
    from pathlib import Path
    data_path = Path(directory) / "metrics.csv"
    with data_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    rows[0][field] = value
    with data_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match=message):
        analyze_algorithm_experiment(path)
    assert not (path.parent / "analysis").exists()
