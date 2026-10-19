"""Confirm the frozen E5 candidate with five training seeds and fresh test seeds."""

import argparse
from concurrent.futures import ProcessPoolExecutor
import dataclasses
from datetime import datetime
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from common.checkpoint import read_checkpoint
from common.config import Config
from common.metrics import write_json
from evaluate import evaluate
from experiments.algorithm_experiment.run import summarize_by_algorithm
from train import train


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_final_experiment(source_comparison, *, output_dir="results/final_experiments",
                         test_seed=30000, jobs=2, official=True):
    source_path = Path(source_comparison).resolve()
    source = read_json(source_path)
    p = source["protocol"]
    require(source["status"] == "completed" and source["selected_algorithm"] == "dqn",
            "Source must be completed and select DQN")
    require(p["environment_revision"] == "tail_occupancy_fixed", "Environment revision mismatch")
    config = Config(**p["base_config"])
    require((config.algorithm, config.state_mode, config.reward_mode, config.epsilon_decay)
            == ("dqn", "v2", "sparse", 0.9999), "Frozen final candidate mismatch")
    require(type(jobs) is int and jobs > 0 and config.device == "cpu", "Positive jobs and CPU required")
    episodes = p["num_episodes"]
    require(type(test_seed) is int and 0 <= test_seed <= 2 ** 32 - episodes, "Invalid test seed range")
    for old_seed in (p["eval_seed"], p.get("holdout_seed")):
        require(old_seed is None or abs(test_seed - old_seed) >= episodes, "Test seeds overlap used evaluation seeds")
    if official:
        expected = dataclasses.asdict(Config(state_mode="v2"))
        require({k: v for k, v in dataclasses.asdict(config).items() if k != "seed"}
                == {k: v for k, v in expected.items() if k != "seed"}, "Official frozen configuration mismatch")
        require(p["run_type"] == "official" and p["total_steps"] == 100000 and episodes == 50
                and test_seed == 30000, "Official protocol must preserve budget and predeclared test seeds")
    reused = [dict(run) for run in source["training_runs"] if run["algorithm"] == "dqn"]
    require(len(reused) == 3 and {run["seed"] for run in reused} == {42, 43, 44}, "Reuse exactly seeds 42/43/44")
    hashes = {str(source_path): fingerprint(source_path)}
    for run in reused:
        directory = (source_path.parent / run["run_dir"]).resolve()
        checkpoint_path = (source_path.parent / run["checkpoint"]).resolve()
        saved_config = read_json(directory / "config.json")
        summary = read_json(directory / "summary.json")
        checkpoint = read_checkpoint(checkpoint_path)
        expected_config = dataclasses.asdict(dataclasses.replace(config, algorithm="dqn", seed=run["seed"]))
        require(saved_config == checkpoint["config"] == expected_config, "Reused configuration mismatch")
        require(run["status"] == summary["status"] == "completed", "Reused training incomplete")
        require(run["global_step"] == summary["global_step"] == checkpoint["global_step"] == p["total_steps"],
                "Reused training budget mismatch")
        run.update(run_dir=str(directory), checkpoint=str(checkpoint_path), reused=True)
        for path in (checkpoint_path, *(directory / name for name in ("config.json", "metrics.csv", "summary.json"))):
            hashes[str(path)] = fingerprint(path)

    root = Path(output_dir).resolve() / f"e6_{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=False)
    path = root / "algorithm_comparison.json"
    result = {"status": "running", "error": None, "run_id": root.name,
              "source_comparison": str(source_path), "source_sha256_before": hashes,
              "protocol": {"run_type": "official" if official else "debug",
                "base_config": dataclasses.asdict(config), "algorithms": ["dqn"],
                "seeds": [42, 43, 44, 45, 46], "total_steps": p["total_steps"],
                "num_episodes": episodes, "eval_seed": p["eval_seed"], "holdout_seed": test_seed,
                "torch_threads": p["torch_threads"], "jobs": jobs,
                "environment_revision": p["environment_revision"], "std_ddof": 0,
                "selection_rule": "Candidate frozen from E5; reference checkpoint fixed to seed42 before final test; no reselection",
                "reference_seed": 42, "new_training_seeds": [45, 46], "reused_training_seeds": [42, 43, 44]},
              "training_runs": sorted(reused, key=lambda run: run["seed"]),
              "algorithms": {}, "selected_algorithm": "dqn"}
    write_json(path, result)
    try:
        candidates = [dataclasses.replace(config, seed=seed) for seed in (45, 46)]
        settings = dict(output_dir=root / "logs", experiment="e6", total_steps=p["total_steps"],
                        torch_threads=p["torch_threads"])
        pool = ProcessPoolExecutor(max_workers=min(jobs, 2)) if jobs > 1 else None
        try:
            if pool is not None:
                futures = [pool.submit(train, candidate, **settings) for candidate in candidates]
                outputs = (future.result() for future in futures)
            else:
                outputs = (train(candidate, **settings) for candidate in candidates)
            for seed, (directory, status) in zip((45, 46), outputs):
                summary = read_json(directory / "summary.json")
                result["training_runs"].append({"algorithm": "dqn", "seed": seed, "status": status,
                    "run_dir": str(directory), "checkpoint": str(directory / "checkpoint.pt"), "reused": False,
                    "global_step": summary["global_step"], "update_count": summary["update_count"],
                    "final_epsilon": summary["epsilon"]})
                write_json(path, result)
                if status != "completed":
                    raise InterruptedError("New training incomplete")
        finally:
            if pool is not None:
                pool.shutdown(wait=True, cancel_futures=True)
        for key, seed, summary_key in (("evaluation_dir", p["eval_seed"], "algorithms"),
                                        ("holdout_evaluation_dir", test_seed, "holdout_algorithms")):
            directory = evaluate([run["checkpoint"] for run in result["training_runs"]],
                                 num_episodes=episodes, eval_seed=seed, compare_random=True,
                                 output_dir=root / "evaluations", torch_threads=p["torch_threads"])
            summary = read_json(directory / "summary.json")
            require(summary["status"] == "completed", "Evaluation incomplete")
            result[key] = str(directory)
            result[summary_key] = summarize_by_algorithm(summary)
            write_json(path, result)
        require(all(fingerprint(Path(file)) == value for file, value in hashes.items()), "Reused source changed")
        result["source_unchanged_after_run"] = True
        reference = next(run["checkpoint"] for run in result["training_runs"] if run["seed"] == 42)
        write_json(root / "final_config.json", {"config": dataclasses.asdict(dataclasses.replace(config, seed=42)),
                   "reference_checkpoint": reference, "reference_rule": result["protocol"]["selection_rule"],
                   "all_checkpoints": [run["checkpoint"] for run in result["training_runs"]],
                   "scope": "Best among tested development candidates, not global optimum or convergence proof"})
        result["status"] = "completed"
        write_json(path, result)
    except (Exception, KeyboardInterrupt) as error:
        result["status"] = "interrupted" if isinstance(error, (KeyboardInterrupt, InterruptedError)) else "failed"
        result["error"] = f"{type(error).__name__}: {error}"
        write_json(path, result)
        raise
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_comparison", required=True)
    parser.add_argument("--output_dir", default="results/final_experiments")
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args(argv)
    try:
        print(run_final_experiment(**vars(args)))
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
