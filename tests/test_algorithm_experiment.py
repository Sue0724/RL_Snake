"""算法对比实验只编排公共 train/evaluate，并汇总多个 seed。"""

import json

from experiments.algorithm_experiment.run import (
    run_algorithm_experiment,
    summarize_by_algorithm,
)


def test_summarize_by_algorithm_groups_seeds_and_ignores_random():
    summary = {
        "models": [
            {"model_id": "dqn_1", "algorithm": "dqn", "training_seed": 42,
             "mean_score": 10.0},
            {"model_id": "dqn_2", "algorithm": "dqn", "training_seed": 43,
             "mean_score": 14.0},
            {"model_id": "double_1", "algorithm": "double_dqn", "training_seed": 42,
             "mean_score": 12.0},
            {"model_id": "random", "algorithm": "random", "training_seed": None,
             "mean_score": 0.0},
        ]
    }
    result = summarize_by_algorithm(summary)
    assert result["dqn"] == {
        "num_models": 2, "num_seeds": 2, "mean_score": 12.0,
        "std_of_model_mean_scores": 2.0, "best_model": "dqn_2",
    }
    assert result["double_dqn"]["mean_score"] == 12.0
    assert "random" not in result


def test_experiment_runs_all_algorithms_through_shared_entry_points(tmp_path):
    comparison_path = run_algorithm_experiment(
        algorithms=("dqn", "double_dqn", "dueling_dqn"),
        seeds=(42,),
        total_steps=2,
        num_episodes=1,
        output_dir=tmp_path,
        experiment="debug_algorithm",
    )
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    assert comparison["status"] == "completed"
    assert set(comparison["algorithms"]) == {"dqn", "double_dqn", "dueling_dqn"}
    assert len(comparison["training_runs"]) == 3
    assert all(run["checkpoint"].endswith("checkpoint.pt")
               for run in comparison["training_runs"])
