"""Compare epsilon decay rates with fixed V2, DQN and sparse reward."""

import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import dataclasses
from datetime import datetime
import json
import math
from pathlib import Path
import re
from statistics import mean, pstdev
from uuid import uuid4

from common.config import Config, build_parser, config_from_args
from common.metrics import write_json
from env.snake_env import SnakeEnv
from evaluate import evaluate
from train import positive_int, train, validate_training_config


DEFAULT_DECAYS = (0.9998, 0.9999, 0.99995)


def floor_step(start, end, decay):
    """Completed steps until reaching the floor; None means no finite crossing."""
    if start <= end:
        return 0
    if end == 0 or decay == 1:
        return None
    return math.ceil(math.log(end / start) / math.log(decay))


def run_exploration_experiment(*, config=None, epsilon_decays=DEFAULT_DECAYS,
                               seeds=(42, 43, 44), total_steps=100_000,
                               num_episodes=50, eval_seed=10_000,
                               output_dir="results/exploration_experiments",
                               experiment="debug_exploration", official=False,
                               jobs=1, torch_threads=1):
    config = dataclasses.replace(config) if config is not None else Config(state_mode="v2")
    decays, seeds = tuple(epsilon_decays), tuple(seeds)
    if (not decays or len(set(decays)) != len(decays)
            or any(not math.isfinite(value) or not 0 < value <= 1 for value in decays)):
        raise ValueError("epsilon_decays must be finite, unique and in (0, 1]")
    if (not seeds or len(set(seeds)) != len(seeds)
            or any(type(seed) is not int or not 0 <= seed < 2 ** 32 for seed in seeds)):
        raise ValueError("seeds must be unique integers in [0, 2**32)")
    if (config.algorithm, config.state_mode, config.reward_mode) != ("dqn", "v2", "sparse"):
        raise ValueError("Exploration comparisons fix DQN + V2 + sparse")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", experiment):
        raise ValueError("Invalid experiment name")
    if any(type(value) is not int or value <= 0
           for value in (total_steps, num_episodes, jobs, torch_threads)):
        raise ValueError("Budgets, jobs and threads must be positive integers")
    if type(eval_seed) is not int or not 0 <= eval_seed <= 2 ** 32 - num_episodes:
        raise ValueError("Evaluation seeds must be in [0, 2**32)")
    if jobs > 1 and config.device != "cpu":
        raise ValueError("Parallel training requires CPU")
    if official and (len(seeds) < 3 or len(decays) < 2 or num_episodes < 20):
        raise ValueError("Official comparisons need >=3 seeds, >=2 decay rates and >=20 eval episodes")
    if official and experiment.startswith("debug"):
        raise ValueError("Official experiment names must not start with debug")
    for decay in decays:
        for seed in seeds:
            candidate = dataclasses.replace(config, epsilon_decay=decay, seed=seed)
            validate_training_config(candidate)
            SnakeEnv(candidate).close()

    root = Path(output_dir).expanduser().resolve() / (
        f"{experiment}_{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}"
    )
    root.mkdir(parents=True, exist_ok=False)
    path = root / "comparison.json"
    labels = [str(decay) for decay in decays]
    comparison = {
        "status": "running", "run_id": root.name, "error": None,
        "protocol": {
            "run_type": "official" if official else "debug",
            "base_config": dataclasses.asdict(config), "explorations": labels,
            "epsilon_decays": list(decays), "seeds": list(seeds),
            "total_steps": total_steps, "num_episodes": num_episodes,
            "eval_seed": eval_seed, "jobs": jobs, "torch_threads": torch_threads,
            "primary_metric": "mean_score", "std_ddof": 0,
            "environment_revision": "tail_occupancy_fixed",
            "schedule": "After t completed environment steps: max(end, start * decay**t)",
            "floor_steps": {label: floor_step(config.epsilon_start, config.epsilon_end, decay)
                            for label, decay in zip(labels, decays)},
        },
        "training_runs": [], "evaluation_dirs": {}, "explorations": {},
    }
    write_json(path, comparison)
    evaluations = {}
    try:
        for label, decay in zip(labels, decays):
            checkpoints = []
            candidates = [dataclasses.replace(config, epsilon_decay=decay, seed=seed) for seed in seeds]
            settings = dict(output_dir=root / "logs", total_steps=total_steps,
                            experiment=f"{experiment}_decay{label.replace('.', 'p')}",
                            torch_threads=torch_threads)
            pool = ProcessPoolExecutor(max_workers=min(jobs, len(seeds))) if jobs > 1 else None
            try:
                if pool is not None:
                    futures = [pool.submit(train, candidate, **settings) for candidate in candidates]
                    results = (future.result() for future in futures)
                else:
                    results = (train(candidate, **settings) for candidate in candidates)
                for seed, (directory, status) in zip(seeds, results):
                    checkpoint = directory / "checkpoint.pt"
                    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
                    comparison["training_runs"].append({
                        "exploration": label, "epsilon_decay": decay, "seed": seed, "status": status,
                        "run_dir": directory.relative_to(root).as_posix(),
                        "checkpoint": checkpoint.relative_to(root).as_posix(),
                        "global_step": summary["global_step"], "update_count": summary["update_count"],
                        "final_epsilon": summary["epsilon"],
                    })
                    write_json(path, comparison)
                    if status != "completed":
                        raise InterruptedError(f"Training interrupted: decay={decay}, seed={seed}")
                    checkpoints.append(checkpoint)
            finally:
                if pool is not None:
                    pool.shutdown(wait=True, cancel_futures=True)
            directory = evaluate(checkpoints, num_episodes=num_episodes, eval_seed=eval_seed,
                                 device=config.device, output_dir=root / "evaluations",
                                 torch_threads=torch_threads)
            summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
            if summary["status"] != "completed":
                raise RuntimeError(f"Incomplete evaluation: decay={decay}")
            models = summary["models"]
            evaluations[label] = models
            comparison["evaluation_dirs"][label] = directory.relative_to(root).as_posix()
            comparison["explorations"][label] = {
                "epsilon_decay": decay, "num_seeds": len(models),
                "mean_score": mean(model["mean_score"] for model in models),
                "std_of_model_mean_scores": pstdev(model["mean_score"] for model in models),
                "max_score": max(model["max_score"] for model in models),
                "mean_return": mean(model["mean_return"] for model in models),
                "mean_episode_length": mean(model["mean_episode_length"] for model in models),
                "truncation_rate": mean(model["truncation_rate"] for model in models),
            }
            write_json(path, comparison)
        fields = ("exploration", "training_seed", "mean_score", "std_score", "max_score",
                  "mean_return", "mean_episode_length", "truncation_rate")
        with (root / "comparison.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for label, models in evaluations.items():
                for model in models:
                    writer.writerow({"exploration": label, **{key: model[key] for key in fields[1:]}})
        comparison["status"] = "completed"
        write_json(path, comparison)
    except (Exception, KeyboardInterrupt) as error:
        comparison["status"] = (
            "interrupted" if isinstance(error, (KeyboardInterrupt, InterruptedError)) else "failed"
        )
        comparison["error"] = f"{type(error).__name__}: {error}"
        write_json(path, comparison)
        raise
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epsilon_decays", type=float, nargs="+", default=DEFAULT_DECAYS)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    parser.add_argument("--total_steps", type=positive_int, default=100_000)
    parser.add_argument("--eval_episodes", type=positive_int, default=50)
    parser.add_argument("--eval_seed", type=int, default=10_000)
    parser.add_argument("--output_dir", default="results/exploration_experiments")
    parser.add_argument("--experiment", default="debug_exploration")
    parser.add_argument("--official", action="store_true")
    parser.add_argument("--jobs", type=positive_int, default=1)
    parser.add_argument("--torch_threads", type=positive_int, default=1)
    parser = build_parser(parser=parser)
    parser.set_defaults(state_mode="v2")
    args = parser.parse_args(argv)
    if args.seed is not None or args.epsilon_decay is not None or args.num_episodes is not None:
        parser.error("Use --seeds, --epsilon_decays and --eval_episodes; training uses --total_steps")
    try:
        path = run_exploration_experiment(
            config=config_from_args(args), epsilon_decays=args.epsilon_decays, seeds=args.seeds,
            total_steps=args.total_steps, num_episodes=args.eval_episodes, eval_seed=args.eval_seed,
            output_dir=args.output_dir, experiment=args.experiment, official=args.official,
            jobs=args.jobs, torch_threads=args.torch_threads,
        )
    except ValueError as error:
        parser.error(str(error))
    print(f"Exploration comparison saved: {path}", flush=True)


if __name__ == "__main__":
    main()
