"""复用公共 train/evaluate 的算法对比实验编排，不实现第二套训练循环。"""

import argparse
import json
from pathlib import Path
from statistics import pstdev

from common.config import Config
from common.metrics import write_json
from evaluate import evaluate
from train import train


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
):
    """训练算法×seed 网格，随后在相同评估种子上统一评估。"""
    algorithms = tuple(algorithms)
    seeds = tuple(seeds)
    if not algorithms or any(name not in ALGORITHMS for name in algorithms):
        raise ValueError(f"algorithms 只能取 {', '.join(ALGORITHMS)} 的非空子集")
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("seeds 必须是非空且不重复的整数序列")
    if total_steps <= 0 or num_episodes <= 0 or torch_threads <= 0:
        raise ValueError("total_steps、num_episodes 和 torch_threads 必须大于 0")

    output_root = Path(output_dir).expanduser().resolve()
    training_runs = []
    for algorithm in algorithms:
        for seed in seeds:
            config = Config(algorithm=algorithm, seed=seed)
            run_dir, status = train(
                config,
                output_dir=output_root / "logs",
                experiment=experiment,
                total_steps=total_steps,
                torch_threads=torch_threads,
            )
            if status != "completed":
                raise RuntimeError(f"{algorithm} seed={seed} 训练状态为 {status}")
            training_runs.append({
                "algorithm": algorithm,
                "seed": seed,
                "run_dir": str(run_dir),
                "checkpoint": str(run_dir / "checkpoint.pt"),
            })

    evaluation_dir = evaluate(
        [run["checkpoint"] for run in training_runs],
        num_episodes=num_episodes,
        eval_seed=eval_seed,
        compare_random=True,
        output_dir=output_root / "evaluations",
        torch_threads=torch_threads,
    )
    evaluation_summary = json.loads(
        (evaluation_dir / "summary.json").read_text(encoding="utf-8")
    )
    comparison = {
        "status": "completed",
        "protocol": {
            "algorithms": list(algorithms),
            "seeds": list(seeds),
            "total_steps": total_steps,
            "num_episodes": num_episodes,
            "eval_seed": eval_seed,
            "torch_threads": torch_threads,
        },
        "training_runs": training_runs,
        "evaluation_dir": str(evaluation_dir),
        "algorithms": summarize_by_algorithm(evaluation_summary),
    }
    comparison_path = evaluation_dir / "algorithm_comparison.json"
    write_json(comparison_path, comparison)
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
    args = parser.parse_args(argv)
    try:
        path = run_algorithm_experiment(**vars(args))
    except ValueError as error:
        parser.error(str(error))
    print(f"算法对比完成：{path}", flush=True)


if __name__ == "__main__":
    main()
