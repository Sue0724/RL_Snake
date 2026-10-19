"""Compare V1/V2 using DQN, sparse reward and identical training budgets."""

import argparse
import csv
import dataclasses
from datetime import datetime
import json
from pathlib import Path
import re
from statistics import mean, pstdev
from uuid import uuid4

from algorithms.factory import create_agent
from common.config import Config, build_parser, config_from_args
from common.metrics import write_json
from env.snake_env import STATE_DIMS, SnakeEnv
from evaluate import evaluate
from train import positive_int, train, validate_training_config


def run_state_experiment(*, config=None, state_modes=("v1", "v2"), seeds=(42, 43, 44),
                         total_steps=100_000, num_episodes=50, eval_seed=10_000,
                         output_dir="results/state_experiments", experiment="debug_state",
                         official=False, torch_threads=1):
    config = dataclasses.replace(config) if config is not None else Config()
    state_modes, seeds = tuple(state_modes), tuple(seeds)
    if (not state_modes or len(set(state_modes)) != len(state_modes)
            or any(mode not in STATE_DIMS for mode in state_modes)):
        raise ValueError("state_modes must be a unique nonempty subset of v1/v2")
    if (not seeds or len(set(seeds)) != len(seeds)
            or any(type(seed) is not int or not 0 <= seed < 2 ** 32 for seed in seeds)):
        raise ValueError("seeds must be unique integers in [0, 2**32)")
    if config.algorithm != "dqn" or config.reward_mode != "sparse":
        raise ValueError("State experiments fix algorithm=dqn and reward_mode=sparse")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", experiment):
        raise ValueError("experiment must contain only letters, digits, underscores and hyphens")
    if any(type(value) is not int or value <= 0
           for value in (total_steps, num_episodes, torch_threads)):
        raise ValueError("Budgets, evaluation episodes and threads must be positive integers")
    if type(eval_seed) is not int or not 0 <= eval_seed <= 2 ** 32 - num_episodes:
        raise ValueError("Evaluation seeds must all be in [0, 2**32)")
    if official and (len(seeds) < 3 or len(state_modes) != 2 or num_episodes < 20):
        raise ValueError("Official comparisons require both states, >=3 seeds and >=20 eval episodes")
    if official and experiment.startswith("debug"):
        raise ValueError("An official experiment name must not start with debug")

    parameter_counts = {}
    for mode in state_modes:
        for seed in seeds:
            candidate = dataclasses.replace(config, state_mode=mode, seed=seed)
            validate_training_config(candidate)
            env = SnakeEnv(candidate)
            try:
                if mode not in parameter_counts:
                    agent = create_agent(env.state_dim, env.n_actions, candidate)
                    parameter_counts[mode] = sum(p.numel() for p in agent.online_net.parameters())
            finally:
                env.close()

    run_id = f"{experiment}_{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}"
    root = Path(output_dir).expanduser().resolve() / run_id
    root.mkdir(parents=True, exist_ok=False)
    path = root / "comparison.json"
    comparison = {
        "run_id": run_id, "status": "running", "error": None,
        "protocol": {
            "run_type": "official" if official else "debug",
            "base_config": dataclasses.asdict(config), "state_modes": list(state_modes),
            "seeds": list(seeds), "total_steps": total_steps,
            "num_episodes": num_episodes, "eval_seed": eval_seed,
            "torch_threads": torch_threads, "primary_metric": "mean_score", "std_ddof": 0,
            "parameter_counts": parameter_counts,
            "environment_revision": "tail_occupancy_fixed",
        },
        "training_runs": [], "evaluation_dirs": {}, "state_modes": {},
    }
    write_json(path, comparison)
    evaluations = {}
    try:
        for mode in state_modes:
            checkpoints = []
            for seed in seeds:
                candidate = dataclasses.replace(config, state_mode=mode, seed=seed)
                run_dir, status = train(candidate, output_dir=root / "logs",
                                        experiment=experiment, total_steps=total_steps,
                                        torch_threads=torch_threads)
                checkpoint = run_dir / "checkpoint.pt"
                comparison["training_runs"].append({
                    "state_mode": mode, "seed": seed, "status": status,
                    "run_dir": run_dir.relative_to(root).as_posix(),
                    "checkpoint": checkpoint.relative_to(root).as_posix(),
                })
                write_json(path, comparison)
                if status != "completed":
                    raise InterruptedError(f"Training interrupted: {mode}, seed={seed}")
                checkpoints.append(checkpoint)
            directory = evaluate(checkpoints, num_episodes=num_episodes, eval_seed=eval_seed,
                                 device=config.device, output_dir=root / "evaluations",
                                 torch_threads=torch_threads)
            summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
            if summary["status"] != "completed":
                raise RuntimeError(f"Incomplete evaluation: {mode}")
            models = summary["models"]
            evaluations[mode] = models
            comparison["evaluation_dirs"][mode] = directory.relative_to(root).as_posix()
            comparison["state_modes"][mode] = {
                "num_seeds": len(models), "parameter_count": parameter_counts[mode],
                "mean_score": mean(model["mean_score"] for model in models),
                "std_of_model_mean_scores": pstdev(model["mean_score"] for model in models),
                "max_score": max(model["max_score"] for model in models),
                "mean_return": mean(model["mean_return"] for model in models),
                "mean_episode_length": mean(model["mean_episode_length"] for model in models),
                "truncation_rate": mean(model["truncation_rate"] for model in models),
            }
            write_json(path, comparison)
        fields = ("state_mode", "training_seed", "mean_score", "std_score", "max_score",
                  "mean_return", "mean_episode_length", "truncation_rate")
        with (root / "comparison.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for mode, models in evaluations.items():
                for model in models:
                    writer.writerow({"state_mode": mode, **{key: model[key] for key in fields[1:]}})
        comparison["status"] = "completed"
        write_json(path, comparison)
    except (Exception, KeyboardInterrupt) as error:
        comparison["status"] = (
            "interrupted" if isinstance(error, (InterruptedError, KeyboardInterrupt)) else "failed"
        )
        comparison["error"] = f"{type(error).__name__}: {error}"
        write_json(path, comparison)
        raise
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state_modes", nargs="+", choices=tuple(STATE_DIMS), default=("v1", "v2"))
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--total_steps", type=positive_int, default=100_000)
    parser.add_argument("--eval_episodes", type=positive_int, default=50)
    parser.add_argument("--eval_seed", type=int, default=10_000)
    parser.add_argument("--output_dir", default="results/state_experiments")
    parser.add_argument("--experiment", default="debug_state")
    parser.add_argument("--official", action="store_true")
    parser.add_argument("--torch_threads", type=positive_int, default=1)
    args = build_parser(parser=parser).parse_args(argv)
    if args.seed is not None or args.state_mode is not None or args.num_episodes is not None:
        parser.error("Use --seeds, --state_modes and --eval_episodes; training uses --total_steps")
    try:
        path = run_state_experiment(
            config=config_from_args(args), state_modes=args.state_modes, seeds=args.seeds,
            total_steps=args.total_steps, num_episodes=args.eval_episodes, eval_seed=args.eval_seed,
            output_dir=args.output_dir, experiment=args.experiment, official=args.official,
            torch_threads=args.torch_threads,
        )
    except ValueError as error:
        parser.error(str(error))
    print(f"State comparison saved: {path}", flush=True)


if __name__ == "__main__":
    main()
