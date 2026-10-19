"""Replay evaluation seeds and record exact cycles, idle gaps and collision types."""

import argparse
import csv
import dataclasses
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
from uuid import uuid4

import torch

from algorithms.factory import load_agent
from common.metrics import REWARD_FIELDS, write_json
from env.snake_env import SnakeEnv


def render_examples(examples, output, board_size):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.patches import Rectangle

    count = len(examples)
    fig, axes = plt.subplots((count + 2) // 3, 3, figsize=(12, 4 * ((count + 2) // 3)),
                             squeeze=False, layout="constrained")
    for ax in axes.flat:
        ax.set_visible(False)
    for ax, example in zip(axes.flat, examples.values()):
        ax.set_visible(True)
        row, frame = example["metrics"], example["trace"][-1]
        for r, c in frame["body"]:
            ax.add_patch(Rectangle((c, r), 1, 1, facecolor="#23866B", edgecolor="white"))
        hr, hc = frame["head"]
        ax.add_patch(Rectangle((hc, hr), 1, 1, facecolor="#173D48", edgecolor="white"))
        fr, fc = frame["food"]
        ax.scatter([fc + 0.5], [fr + 0.5], color="#D34F3F", s=55, zorder=3)
        dr, dc = {"up": (-1, 0), "right": (0, 1), "down": (1, 0), "left": (0, -1)}[frame["direction"]]
        if frame["action"] == 1:
            dr, dc = -dc, dr
        elif frame["action"] == 2:
            dr, dc = dc, -dr
        ax.annotate("", xy=(hc + dc + 0.5, hr + dr + 0.5), xytext=(hc + 0.5, hr + 0.5),
                    arrowprops={"arrowstyle": "->", "color": "#E6A51C", "lw": 2})
        ax.set(xlim=(-0.75, board_size + 0.75), ylim=(board_size + 0.75, -0.75), aspect="equal")
        ax.set_xticks(range(board_size + 1))
        ax.set_yticks(range(board_size + 1))
        ax.grid(alpha=0.2)
        ax.tick_params(labelsize=7)
        ax.set_title(f"{row['reward_mode']} | train {row['training_seed']} | eval {row['evaluation_seed']}\n"
                     f"Before final action {frame['step'] + 1}: {row['outcome']}, score={row['score']}", fontsize=9)
    fig.suptitle("Diagnostic examples: first occurrence per outcome; arrow = attempted action", fontsize=12)
    fig.savefig(output / "examples.png", dpi=150)
    plt.close(fig)


@torch.inference_mode()
def trace_episode(agent, config, seed):
    env = SnakeEnv(dataclasses.replace(config, render_mode=None))
    try:
        state, _ = env.reset(seed=seed)
        seen, trace = {}, []
        cycle_start = cycle_period = None
        last_food_step = max_idle = 0
        rewards = dict.fromkeys(REWARD_FIELDS, 0.0)
        episode_return = 0.0
        while True:
            key = (tuple(env.body), env.direction, env.food)
            if cycle_period is None and key in seen:
                cycle_start = seen[key]
                cycle_period = env.steps - cycle_start
            seen.setdefault(key, env.steps)
            action = agent.select_action(state, training=False)
            head, direction = env.body[0], env.direction
            trace.append({"step": env.steps, "head": head, "direction": direction,
                          "food": env.food, "body": tuple(env.body),
                          "score": env.score, "action": action})
            old_score = env.score
            state, reward, terminated, truncated, info = env.step(action)
            episode_return += reward
            for name in REWARD_FIELDS:
                rewards[name] += info[name]
            if info["score"] > old_score:
                last_food_step = env.steps
            max_idle = max(max_idle, env.steps - last_food_step)
            if terminated or truncated:
                outcome = "timeout" if truncated else "win"
                if info["death_penalty"] < 0:
                    # Collision attempts do not move the head; infer the attempted cell.
                    delta = {"up": (-1, 0), "right": (0, 1), "down": (1, 0), "left": (0, -1)}
                    dr, dc = delta[direction]
                    if action == 1:
                        dr, dc = -dc, dr
                    elif action == 2:
                        dr, dc = dc, -dr
                    row, col = head[0] + dr, head[1] + dc
                    outcome = "wall" if not (0 <= row < env.n_rows and 0 <= col < env.n_cols) else "self"
                return {
                    "evaluation_seed": seed, "score": info["score"],
                    "episode_length": info["steps"], "episode_return": episode_return,
                    "outcome": outcome, "terminated": terminated, "truncated": truncated,
                    "cycle_detected": cycle_period is not None,
                    "cycle_start": cycle_start, "cycle_period": cycle_period,
                    "max_steps_without_food": max_idle,
                    "tail_steps_without_food": env.steps - last_food_step,
                    **rewards,
                }, trace
    finally:
        env.close()


def analyze_behavior(comparison_path):
    root = Path(comparison_path).resolve().parent
    comparison = json.loads((root / "comparison.json").read_text(encoding="utf-8"))
    if comparison["status"] != "completed":
        raise ValueError("Behavior analysis requires a completed comparison")
    torch.set_num_threads(comparison["protocol"]["torch_threads"])
    seeds = range(comparison["protocol"]["eval_seed"],
                  comparison["protocol"]["eval_seed"] + comparison["protocol"]["num_episodes"])
    output = root / "behavior" / f"analysis_{datetime.now():%Y%m%d_%H%M%S}_{uuid4().hex[:8]}"
    output.mkdir(parents=True, exist_ok=False)
    rows, examples, hashes = [], {}, {}
    expected = {}
    for mode, directory in comparison["evaluation_dirs"].items():
        with (root / directory / "metrics.csv").open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                expected[(mode, int(row["training_seed"]), int(row["evaluation_seed"]))] = row
    for run in comparison["training_runs"]:
        checkpoint = root / run["checkpoint"]
        before = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        agent, config = load_agent(checkpoint)
        mode = run["reward_mode"]
        print(f"Behavior replay: {mode} seed={run['seed']}", flush=True)
        for seed in seeds:
            row, trace = trace_episode(agent, config, seed)
            row.update(reward_mode=mode, training_seed=run["seed"])
            original = expected[(mode, run["seed"], seed)]
            for name in ("score", "episode_length", "episode_return", *REWARD_FIELDS):
                if not math.isclose(row[name], float(original[name]), abs_tol=1e-7):
                    raise RuntimeError(f"Replay mismatch: {mode}, train={run['seed']}, eval={seed}, {name}")
            if any(str(row[name]) != original[name] for name in ("terminated", "truncated")):
                raise RuntimeError("Replay termination flags differ from original evaluation")
            rows.append(row)
            # Retain the first occurrence of each outcome and first exact cycle, not the best seed.
            labels = [row["outcome"]] + (["cycle"] if row["cycle_detected"] else [])
            for label in labels:
                key = f"{mode}_{label}"
                if key not in examples:
                    examples[key] = {"metrics": row, "checkpoint": run["checkpoint"], "trace": trace}
        if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != before:
            raise RuntimeError(f"Source checkpoint changed during replay: {checkpoint}")
        hashes[run["checkpoint"]] = before

    if len(rows) != len(expected):
        raise RuntimeError("Replay episode count differs from original evaluation")

    summaries = {}
    for mode in comparison["protocol"]["reward_modes"]:
        group = [row for row in rows if row["reward_mode"] == mode]
        summaries[mode] = {
            "episodes": len(group), "mean_score": mean(row["score"] for row in group),
            "outcomes": {name: sum(row["outcome"] == name for row in group)
                         for name in ("wall", "self", "timeout", "win")},
            "exact_cycle_episodes": sum(row["cycle_detected"] for row in group),
            "zero_food_timeouts": sum(row["truncated"] and row["score"] == 0 for row in group),
            "mean_max_steps_without_food": mean(row["max_steps_without_food"] for row in group),
            "max_steps_without_food": max(row["max_steps_without_food"] for row in group),
        }
        if abs(summaries[mode]["mean_score"] - comparison["reward_modes"][mode]["mean_score"]) > 1e-9:
            raise RuntimeError(f"Replay scores do not match original evaluation for {mode}")
    with (output / "metrics.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    write_json(output / "examples.json", examples)
    render_examples(examples, output, comparison["protocol"]["base_config"]["board_size"])
    write_json(output / "summary.json", {
        "status": "completed", "protocol": comparison["protocol"],
        "cycle_definition": "Repeated full body, direction and food under a fixed greedy policy",
        "source_checkpoint_sha256": hashes, "reward_modes": summaries,
    })
    return output / "summary.json"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", required=True)
    args = parser.parse_args(argv)
    print(analyze_behavior(args.comparison))


if __name__ == "__main__":
    main()
