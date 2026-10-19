"""复用公共 train/evaluate 的算法对比实验编排，不实现第二套训练循环。"""

import argparse
from concurrent.futures import ProcessPoolExecutor
import dataclasses
from datetime import datetime
import json
from pathlib import Path
import re
from statistics import pstdev
from uuid import uuid4

from common.config import Config
from common.metrics import write_json
from evaluate import evaluate
from train import train, validate_training_config


ALGORITHMS = ("dqn", "double_dqn", "dueling_dqn")


def positive_int(text):
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("必须为正整数")
    return value


def summarize_by_algorithm(evaluation_summary):
    """按算法汇总多个 seed 的模型平均分，Random 不参与算法排名。"""
    groups = {}
    for model in evaluation_summary["models"]:
        if model["algorithm"] == "random":
            continue
        groups.setdefault(model["algorithm"], []).append(model)

    result = {}
    for algorithm, models in groups.items():
        means = [model["mean_score"] for model in models]
        result[algorithm] = {
            "num_models": len(models),
            "num_seeds": len({model["training_seed"] for model in models}),
            "mean_score": sum(means) / len(means),
            "std_of_model_mean_scores": pstdev(means) if len(means) > 1 else 0.0,
            "best_model": max(models, key=lambda model: model["mean_score"])["model_id"],
        }
    return result


def run_algorithm_experiment(
    *,
    algorithms=ALGORITHMS,
    seeds=(42, 43, 44),
    total_steps=100_000,
    num_episodes=50,
    eval_seed=10_000,
    output_dir="results",
    experiment="algorithm",
    torch_threads=1,
    config=None,
    jobs=1,
    official=False,
    holdout_seed=None,
):
    """训练算法×seed 网格，随后在相同评估种子上统一评估。"""
    algorithms = tuple(algorithms)
    seeds = tuple(seeds)
    config = dataclasses.replace(config) if config is not None else Config()
    if (not algorithms or len(set(algorithms)) != len(algorithms)
            or any(name not in ALGORITHMS for name in algorithms)):
        raise ValueError(f"algorithms 只能取 {', '.join(ALGORITHMS)} 的非空子集")
    if (not seeds or len(set(seeds)) != len(seeds)
            or any(type(seed) is not int or not 0 <= seed < 2 ** 32 for seed in seeds)):
        raise ValueError("seeds 必须是非空且不重复的整数序列")
    if any(type(value) is not int or value <= 0
           for value in (total_steps, num_episodes, torch_threads, jobs)):
        raise ValueError("total_steps、num_episodes 和 torch_threads 必须大于 0")

    for value in (eval_seed, holdout_seed):
        if value is not None and (type(value) is not int or not 0 <= value <= 2 ** 32 - num_episodes):
            raise ValueError("Evaluation seed range is invalid")
    if eval_seed is None:
        raise ValueError("eval_seed must be an integer")
    if holdout_seed is not None and abs(holdout_seed - eval_seed) < num_episodes:
        raise ValueError("Development and holdout seeds must not overlap")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", experiment):
        raise ValueError("Invalid experiment name")
    if jobs > 1 and config.device != "cpu":
        raise ValueError("Parallel training requires CPU")
    if official and (len(seeds) < 3 or len(algorithms) < 2 or num_episodes < 20
                     or experiment.startswith("debug")):
        raise ValueError("Official comparisons need >=3 seeds, >=2 algorithms and >=20 episodes")
    for algorithm in algorithms:
        for seed in seeds:
            validate_training_config(dataclasses.replace(config, algorithm=algorithm, seed=seed))

    output_root = Path(output_dir).expanduser().resolve() / (
        f"{experiment}_{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}"
    )
    output_root.mkdir(parents=True, exist_ok=False)
    training_runs = []
    comparison = {
        "status": "running", "error": None, "run_id": output_root.name,
        "protocol": {
            "run_type": "official" if official else "debug",
            "base_config": dataclasses.asdict(config),
            "algorithms": list(algorithms),
            "seeds": list(seeds),
            "total_steps": total_steps,
            "num_episodes": num_episodes,
            "eval_seed": eval_seed,
            "torch_threads": torch_threads,
            "jobs": jobs, "holdout_seed": holdout_seed,
            "environment_revision": "tail_occupancy_fixed",
            "primary_metric": "mean_score", "std_ddof": 0,
            "selection_rule": "Highest development mean score; ties use algorithm input order; no holdout reselection",
        },
        "training_runs": training_runs,
        "evaluation_dir": None, "algorithms": {},
    }
    comparison_path = output_root / "algorithm_comparison.json"
    write_json(comparison_path, comparison)
    try:
        for algorithm in algorithms:
            candidates = [dataclasses.replace(config, algorithm=algorithm, seed=seed) for seed in seeds]
            settings = dict(output_dir=output_root / "logs", experiment=experiment,
                            total_steps=total_steps, torch_threads=torch_threads)
            pool = ProcessPoolExecutor(max_workers=min(jobs, len(seeds))) if jobs > 1 else None
            try:
                if pool is not None:
                    futures = [pool.submit(train, candidate, **settings) for candidate in candidates]
                    results = (future.result() for future in futures)
                else:
                    results = (train(candidate, **settings) for candidate in candidates)
                for seed, (run_dir, status) in zip(seeds, results):
                    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
                    training_runs.append({
                        "algorithm": algorithm, "seed": seed, "status": status,
                        "run_dir": str(run_dir), "checkpoint": str(run_dir / "checkpoint.pt"),
                        "global_step": summary["global_step"], "update_count": summary["update_count"],
                        "final_epsilon": summary["epsilon"],
                    })
                    write_json(comparison_path, comparison)
                    if status != "completed":
                        raise InterruptedError(f"{algorithm} seed={seed}: {status}")
            finally:
                if pool is not None:
                    pool.shutdown(wait=True, cancel_futures=True)

        settings = dict(num_episodes=num_episodes, compare_random=True, device=config.device,
                        output_dir=output_root / "evaluations", torch_threads=torch_threads)
        checkpoints = [run["checkpoint"] for run in training_runs]
        evaluation_dir = evaluate(checkpoints, eval_seed=eval_seed, **settings)
        summary = json.loads((evaluation_dir / "summary.json").read_text(encoding="utf-8"))
        if summary["status"] != "completed":
            raise RuntimeError("Incomplete development evaluation")
        comparison["evaluation_dir"] = str(evaluation_dir)
        comparison["algorithms"] = summarize_by_algorithm(summary)
        comparison["selected_algorithm"] = max(algorithms, key=lambda name: comparison["algorithms"][name]["mean_score"])
        write_json(comparison_path, comparison)
        if holdout_seed is not None:
            directory = evaluate(checkpoints, eval_seed=holdout_seed, **settings)
            summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
            if summary["status"] != "completed":
                raise RuntimeError("Incomplete holdout evaluation")
            comparison["holdout_evaluation_dir"] = str(directory)
            comparison["holdout_algorithms"] = summarize_by_algorithm(summary)
        comparison["status"] = "completed"
        write_json(comparison_path, comparison)
    except (Exception, KeyboardInterrupt) as error:
        comparison["status"] = "interrupted" if isinstance(error, (KeyboardInterrupt, InterruptedError)) else "failed"
        comparison["error"] = f"{type(error).__name__}: {error}"
        write_json(comparison_path, comparison)
        raise
    return comparison_path


def parse_algorithms(text):
    values = tuple(item.strip() for item in text.split(",") if item.strip())
    invalid = [value for value in values if value not in ALGORITHMS]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"未知算法：{', '.join(invalid)}；可用：{', '.join(ALGORITHMS)}"
        )
    return values


def main(argv=None):
    parser = argparse.ArgumentParser(description="DQN / Double DQN / Dueling DQN 对比实验")
    parser.add_argument("--algorithms", type=parse_algorithms,
                        default=ALGORITHMS, help="逗号分隔；默认三种算法")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    parser.add_argument("--total_steps", type=positive_int, default=100_000)
    parser.add_argument("--num_episodes", type=positive_int, default=50)
    parser.add_argument("--eval_seed", type=int, default=10_000)
    parser.add_argument("--output_dir", default="results")
    parser.add_argument("--experiment", default="algorithm")
    parser.add_argument("--torch_threads", type=positive_int, default=1)
    parser.add_argument("--jobs", type=positive_int, default=1)
    parser.add_argument("--official", action="store_true")
    parser.add_argument("--holdout_seed", type=int)
    parser.add_argument("--state_mode", choices=("v1", "v2"), default="v1")
    args = parser.parse_args(argv)
    try:
        options = vars(args)
        config = Config(state_mode=options.pop("state_mode"))
        path = run_algorithm_experiment(config=config, **options)
    except ValueError as error:
        parser.error(str(error))
    print(f"算法对比完成：{path}", flush=True)


if __name__ == "__main__":
    main()
