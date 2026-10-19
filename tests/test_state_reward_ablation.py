"""Paired factorial contrasts and audited reuse, not fabricated experiment data."""

import json

import numpy as np
import pytest

from common.config import Config
from experiments.state_experiment.run import run_state_experiment
from experiments.reward_experiment.run import run_reward_experiment
from experiments.reward_experiment.ablation import REWARDS, aggregate_ablation, summarize_cells
from experiments.reward_experiment.ablation_plot import plot_ablation


def test_paired_difference_in_differences():
    rows = []
    for state, values in (("v1", (10, 12, 13)), ("v2", (15, 14, 19))):
        for reward, value in zip(REWARDS, values):
            for index, seed in enumerate((42, 43, 44)):
                score = value + (index if state == "v2" and reward == "distance" else 0)
                rows.append(dict(state_mode=state, reward_mode=reward, training_seed=seed, mean_score=score))
    cells, effects = summarize_cells(rows, [42, 43, 44])
    assert cells["v1/sparse"]["mean_score"] == 10
    assert effects["distance"]["per_seed_interaction"] == [-3, -2, -1]
    assert effects["distance"]["mean_interaction"] == -2
    assert effects["distance"]["std_of_paired_interactions"] == pytest.approx(np.std([-3, -2, -1]))
    assert effects["distance_step"]["mean_interaction"] == 1
    with pytest.raises(ValueError, match="factorial grid"):
        summarize_cells(rows + [rows[0]], [42, 43, 44])
    with pytest.raises(ValueError, match="factorial grid"):
        summarize_cells(rows[:-1], [42, 43, 44])


@pytest.fixture
def sources(tmp_path):
    config = Config(hidden_dim=8, max_steps_per_episode=5, min_buffer_size=2, batch_size=4, buffer_size=16)
    settings = dict(config=config, seeds=(42,), total_steps=8, num_episodes=2, output_dir=tmp_path / "sources")
    state = run_state_experiment(state_modes=("v1",), **settings)
    v1 = run_reward_experiment(reward_modes=REWARDS[1:], **settings)
    config.state_mode = "v2"
    v2 = run_reward_experiment(reward_modes=REWARDS, **settings)
    return state, v2, v1


def test_complete_grid_reuses_explicit_sources_and_generates_plots(tmp_path, sources):
    path = aggregate_ablation(*sources, output_dir=tmp_path / "analysis")
    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["status"] == "completed" and len(result["records"]) == 6
    assert result["new_training_models"] == 2 and result["reused_training_models"] == 4
    assert result["evaluation_records"] == 12 and result["source_unchanged_during_audit"]
    assert len(result["cells"]) == 6 and len(result["interactions"]) == 2
    assert len(result["source_sha256"]) > 30
    assert all(path.stat().st_size > 5000 for path in plot_ablation(path, bin_steps=4))
    counts = {row["state_mode"]: row["parameter_count"] for row in result["records"]}
    assert counts["v2"] - counts["v1"] == 72
    second = aggregate_ablation(*sources, output_dir=tmp_path / "analysis")
    assert second != path


@pytest.mark.parametrize("mutation,message", [
    ("unfinished", "incomplete"), ("budget", "budget mismatch"),
    ("revision", "revision mismatch"), ("seeds", "duplicate training seeds"),
    ("common_config", "Cross-source protocol mismatch"),
])
def test_inconsistent_sources_rejected_before_outputs(tmp_path, sources, mutation, message):
    path = sources[2]
    data = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "unfinished":
        data["status"] = "interrupted"
    elif mutation == "budget":
        data["protocol"]["total_steps"] += 1
    elif mutation == "revision":
        data["protocol"]["environment_revision"] = "old_environment"
    elif mutation == "seeds":
        data["training_runs"][1]["seed"] = 43
    else:
        data["protocol"]["torch_threads"] = 2
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        aggregate_ablation(*sources, output_dir=tmp_path / "analysis")
    assert not (tmp_path / "analysis").exists()
