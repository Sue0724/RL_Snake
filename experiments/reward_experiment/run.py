"""Compare reward modes with identical state, algorithm and interaction budgets."""

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor
import dataclasses
from datetime import datetime
import json
from pathlib import Path
import re
from statistics import mean, pstdev
from uuid import uuid4

from common.config import Config, build_parser, config_from_args
from common.metrics import REWARD_FIELDS, write_json
from env.snake_env import REWARD_MODES, SnakeEnv
from evaluate import evaluate
from train import positive_int, train, validate_training_config


def summarize_modes(evaluations):
    result = {}
    for mode, summary in evaluations.items():
        models = summary["models"]
        scores = [model["mean_score"] for model in models]
        result[mode] = {
            "num_seeds": len({model["training_seed"] for model in models}),
            "mean_score": mean(scores),
            "std_of_model_mean_scores": pstdev(scores),
            "max_score": max(model["max_score"] for model in models),
            "mean_return": mean(model["mean_return"] for model in models),
            "mean_episode_length": mean(model["mean_episode_length"] for model in models),
            "truncation_rate": mean(model["truncation_rate"] for model in models),
            "mean_reward_components": {
                name: mean(model["mean_reward_components"][name] for model in models)
                for name in REWARD_FIELDS
            },
        }
    return result


def run_reward_experiment(*, config=None, reward_modes=REWARD_MODES, seeds=(42, 43, 44),
                          total_steps=100_000, num_episodes=50, eval_seed=10_000,
                          output_dir="results/reward_experiments", experiment="debug_reward",
                          official=False, torch_threads=1, jobs=1):
    config = dataclasses.replace(config) if config is not None else Config()
    reward_modes, seeds = tuple(reward_modes), tuple(seeds)
    if (not reward_modes or len(set(reward_modes)) != len(reward_modes)
            or any(mode not in REWARD_MODES for mode in reward_modes)):
        raise ValueError(f"reward_modes must be a nonempty, unique subset of {REWARD_MODES}")
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be nonempty and unique")
    if config.algorithm != "dqn":
        raise ValueError("Reward experiments fix algorithm=dqn; algorithm comparison is separate")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", experiment):
        raise ValueError("experiment must contain only letters, digits, underscores and hyphens")
    for value in (total_steps, num_episodes, torch_threads, jobs):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Step budget, evaluation episodes and threads must be positive integers")
    if jobs > 1 and config.device != "cpu":
        raise ValueError("Parallel training currently requires device=cpu")
    if not isinstance(eval_seed, int) or not 0 <= eval_seed <= 2 ** 32 - num_episodes:
        raise ValueError("Evaluation seeds must all be in [0, 2**32)")
    if official and (len(seeds) < 3 or len(reward_modes) < 2 or num_episodes < 20):
        raise ValueError("Official comparisons need >=3 seeds, >=2 modes and >=20 evaluation episodes")
    if official and experiment.startswith("debug"):
        raise ValueError("Use an experiment name without 'debug' for an official comparison")
    # Validate the entire grid before creating any outputs or starting training.
    for mode in reward_modes:
        for seed in seeds:
            candidate = dataclasses.replace(config, reward_mode=mode, seed=seed)
            validate_training_config(candidate)
            SnakeEnv(candidate).close()

    run_id = f"{experiment}_{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}"
    run_dir = Path(output_dir).expanduser().resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    comparison_path = run_dir / "comparison.json"
    comparison = {
        "status": "running", "run_id": run_id, "error": None,
        "protocol": {
            "run_type": "official" if official else "debug",
            "base_config": dataclasses.asdict(config), "reward_modes": list(reward_modes),
            "seeds": list(seeds), "total_steps": total_steps,
            "num_episodes": num_episodes, "eval_seed": eval_seed,
            "torch_threads": torch_threads,
            "jobs": jobs, "environment_revision": "tail_occupancy_fixed",
            "primary_metric": "mean_score", "std_ddof": 0,
        },
        "training_runs": [], "evaluation_dirs": {}, "reward_modes": {},
    }
    write_json(comparison_path, comparison)
    evaluations = {}
    try:
        for mode in reward_modes:
            checkpoints = []
            settings = dict(output_dir=run_dir / "logs", experiment=experiment,
                            total_steps=total_steps, torch_threads=torch_threads)
            candidates = [dataclasses.replace(config, reward_mode=mode, seed=seed) for seed in seeds]
            if jobs == 1:
                results = (train(candidate, **settings) for candidate in candidates)
                pool = None
            else:
                pool = ProcessPoolExecutor(max_workers=min(jobs, len(seeds)))
                futures = [pool.submit(train, candidate, **settings) for candidate in candidates]
                results = (future.result() for future in futures)
            try:
                for seed, (training_dir, status) in zip(seeds, results):
                    checkpoint = training_dir / "checkpoint.pt"
                    comparison["training_runs"].append({
                        "reward_mode": mode, "seed": seed, "status": status,
                        "run_dir": training_dir.relative_to(run_dir).as_posix(),
                        "checkpoint": checkpoint.relative_to(run_dir).as_posix(),
                    })
                    write_json(comparison_path, comparison)
                    if status != "completed":
                        raise InterruptedError(f"Training interrupted: {mode}, seed={seed}")
                    checkpoints.append(checkpoint)
            finally:
                if pool is not None:
                    pool.shutdown(wait=True, cancel_futures=True)
            # The public evaluator deliberately rejects mixed reward configurations.
            evaluation_dir = evaluate(
                checkpoints, num_episodes=num_episodes, eval_seed=eval_seed,
                device=config.device, output_dir=run_dir / "evaluations",
                torch_threads=torch_threads,
            )
            summary = json.loads((evaluation_dir / "summary.json").read_text(encoding="utf-8"))
            if summary["status"] != "completed":
                raise RuntimeError(f"Incomplete evaluation for {mode}")
            evaluations[mode] = summary
            comparison["evaluation_dirs"][mode] = evaluation_dir.relative_to(run_dir).as_posix()
            comparison["reward_modes"] = summarize_modes(evaluations)
            write_json(comparison_path, comparison)

        with (run_dir / "comparison.csv").open("w", encoding="utf-8", newline="") as stream:
            fields = ["reward_mode", "training_seed", "mean_score", "std_score", "max_score",
                      "mean_return", "mean_episode_length", "truncation_rate", *REWARD_FIELDS]
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for mode, summary in evaluations.items():
                for model in summary["models"]:
                    row = {name: model[name] for name in fields[1:] if name not in REWARD_FIELDS}
                    writer.writerow({"reward_mode": mode, **row, **model["mean_reward_components"]})
        comparison["status"] = "completed"
        write_json(comparison_path, comparison)
    except (Exception, KeyboardInterrupt) as error:
        comparison["status"] = (
            "interrupted" if isinstance(error, (KeyboardInterrupt, InterruptedError)) else "failed"
        )
        comparison["error"] = f"{type(error).__name__}: {error}"
        write_json(comparison_path, comparison)
        raise
    return comparison_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reward_modes", nargs="+", choices=REWARD_MODES, default=REWARD_MODES)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    parser.add_argument("--total_steps", type=positive_int, default=100_000)
    parser.add_argument("--eval_episodes", type=positive_int, default=50)
    parser.add_argument("--eval_seed", type=int, default=10_000)
    parser.add_argument("--output_dir", default="results/reward_experiments")
    parser.add_argument("--experiment", default="debug_reward")
    parser.add_argument("--official", action="store_true")
    parser.add_argument("--torch_threads", type=positive_int, default=1)
    parser.add_argument("--jobs", type=positive_int, default=1)
    args = build_parser(parser=parser).parse_args(argv)
    if args.seed is not None or args.reward_mode is not None or args.num_episodes is not None:
        parser.error("Use --seeds, --reward_modes and --eval_episodes; budget uses --total_steps")
    try:
        path = run_reward_experiment(
            config=config_from_args(args), reward_modes=args.reward_modes, seeds=args.seeds,
            total_steps=args.total_steps, num_episodes=args.eval_episodes, eval_seed=args.eval_seed,
            output_dir=args.output_dir, experiment=args.experiment, official=args.official,
            torch_threads=args.torch_threads,
            jobs=args.jobs,
        )
    except ValueError as error:
        parser.error(str(error))
    print(f"Reward comparison saved: {path}", flush=True)


if __name__ == "__main__":
    main()
