"""独立评估保存的 DQN 模型，可在相同环境种子下比较 Random。"""

import argparse
import csv
import dataclasses
from datetime import datetime
from pathlib import Path
import time
from uuid import uuid4

import numpy as np
import torch

from algorithms.factory import create_agent, load_agent
from common.metrics import write_json
from common.utils import set_global_seed
from env.snake_env import SnakeEnv


ENV_FIELDS = (
    "board_size", "initial_length", "max_steps_per_episode", "initial_head",
    "state_mode", "reward_mode",
)
FIELDS = (
    "model_id", "algorithm", "training_seed", "evaluation_seed", "episode",
    "score", "episode_return", "episode_length", "terminated", "truncated",
)


def positive_int(text):
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("必须为正整数")
    return value


def score_summary(rows):
    scores = [row["score"] for row in rows]
    return {
        "num_episodes": len(rows),
        "mean_score": float(np.mean(scores)),
        "std_score": float(np.std(scores)),
        "max_score": max(scores),
        "mean_return": float(np.mean([r["episode_return"] for r in rows])),
        "mean_episode_length": float(np.mean([r["episode_length"] for r in rows])),
        "truncation_rate": float(np.mean([r["truncated"] for r in rows])),
    }


@torch.inference_mode()
def evaluate_agent(agent, config, seeds, model_id, algorithm, writer, stream):
    """每局显式使用评估种子；只选动作和走环境，不训练、不写回放池。"""
    env = SnakeEnv(config)
    rows = []
    try:
        for episode, seed in enumerate(seeds, start=1):
            state, _ = env.reset(seed=seed)
            # Random 每局独立播种，避免上一局长度影响下一局的动作 RNG。
            policy = create_agent(
                env.state_dim, env.n_actions,
                dataclasses.replace(config, algorithm="random", seed=seed),
            ) if algorithm == "random" else agent
            episode_return = 0.0
            while True:
                action = policy.select_action(state, training=False)
                state, reward, terminated, truncated, info = env.step(action)
                episode_return += reward
                if terminated or truncated:
                    break
            row = {
                "model_id": model_id, "algorithm": algorithm,
                "training_seed": config.seed if algorithm != "random" else None,
                "evaluation_seed": seed, "episode": episode,
                "score": info["score"], "episode_return": episode_return,
                "episode_length": info["steps"], "terminated": terminated,
                "truncated": truncated,
            }
            rows.append(row)
            writer.writerow(row)
            stream.flush()
    finally:
        env.close()
    return rows


def evaluate(checkpoints, *, num_episodes=50, eval_seed=10000, device="cpu",
             compare_random=False, output_dir="results/evaluations", torch_threads=1):
    if num_episodes <= 0 or torch_threads <= 0:
        raise ValueError("num_episodes 和 torch_threads 必须大于 0")
    if not 0 <= eval_seed <= 2 ** 32 - num_episodes:
        raise ValueError("评估种子列表必须全部在 [0, 2**32) 内")
    if not checkpoints:
        raise ValueError("至少提供一个 checkpoint")
    torch.set_num_threads(torch_threads)
    set_global_seed(eval_seed)
    models = []
    expected_environment = None
    for index, checkpoint_path in enumerate(checkpoints, start=1):
        path = Path(checkpoint_path).expanduser().resolve()
        agent, config = load_agent(path, device=device)
        environment = {name: getattr(config, name) for name in ENV_FIELDS}
        if expected_environment is not None and environment != expected_environment:
            raise ValueError("同组评估的环境、状态和奖励配置必须一致，请分组评估")
        expected_environment = environment
        models.append((f"{config.algorithm}_{index}_seed{config.seed}", path, config, agent))

    seeds = list(range(eval_seed, eval_seed + num_episodes))
    run_id = f"evaluate_{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}"
    run_dir = Path(output_dir).expanduser().resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    protocol = {
        "num_episodes": num_episodes, "evaluation_seeds": seeds,
        "device": device, "torch_threads": torch_threads,
        "exploration": False, "network_update": False, "replay_write": False,
        "compare_random": compare_random,
    }
    write_json(run_dir / "config.json", {
        "protocol": protocol,
        "models": [{"model_id": name, "checkpoint": str(path),
                    "config": dataclasses.asdict(config)} for name, path, config, _ in models],
    })
    summary = {"run_id": run_id, "metrics_scope": "evaluation", "status": "running",
               "protocol": protocol, "models": [], "error": None}
    write_json(run_dir / "summary.json", summary)
    print(f"评估输出目录：{run_dir}", flush=True)
    started = time.perf_counter()
    try:
        with (run_dir / "metrics.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            for name, path, config, agent in models:
                rows = evaluate_agent(agent, config, seeds, name, config.algorithm, writer, stream)
                result = {"model_id": name, "algorithm": config.algorithm, "training_seed": config.seed,
                          "checkpoint": str(path), **score_summary(rows)}
                summary["models"].append(result)
                print(f"{name}: 平均得分={result['mean_score']:.2f} "
                      f"标准差={result['std_score']:.2f} 最高分={result['max_score']}", flush=True)
            if compare_random:
                rows = evaluate_agent(None, models[0][2], seeds, "random", "random", writer, stream)
                result = {"model_id": "random", "algorithm": "random",
                          "training_seed": None, "checkpoint": None, **score_summary(rows)}
                summary["models"].append(result)
                print(f"random: 平均得分={result['mean_score']:.2f} "
                      f"标准差={result['std_score']:.2f} 最高分={result['max_score']}", flush=True)
        dqn_results = [r for r in summary["models"] if r["algorithm"] == "dqn"]
        means = [r["mean_score"] for r in dqn_results]
        if means:
            summary["dqn_across_models"] = {
                "num_models": len(means), "mean_score": float(np.mean(means)),
                "std_of_model_mean_scores": float(np.std(means)),
            }
        summary["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        summary["status"] = "interrupted" if isinstance(error, KeyboardInterrupt) else "failed"
        summary["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        summary["wall_clock_time"] = time.perf_counter() - started
        write_json(run_dir / "summary.json", summary)
    print("评估完成；模型文件未被修改。", flush=True)
    return run_dir


def main(argv=None):
    parser = argparse.ArgumentParser(description="DQN 独立贪心评估及 Random 对比")
    parser.add_argument("--checkpoints", "--checkpoint", nargs="+", required=True,
                        help="一个或多个 checkpoint.pt 路径")
    parser.add_argument("--num_episodes", type=positive_int, default=50)
    parser.add_argument("--eval_seed", type=int, default=10000, help="第一局评估种子，之后逐局加 1")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compare_random", action="store_true", help="同时评估相同环境种子下的 Random")
    parser.add_argument("--output_dir", default="results/evaluations")
    parser.add_argument("--torch_threads", type=positive_int, default=1)
    args = parser.parse_args(argv)
    evaluate(**vars(args))


if __name__ == "__main__":
    main()
