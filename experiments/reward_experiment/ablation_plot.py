"""Regenerate factorial state/reward figures from audited artifacts."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np

from experiments.plotting import COMPARISON_COLORS, plot_main, training_bins


def plot_ablation(comparison_path, bin_steps=5000):
    if type(bin_steps) is not int or bin_steps <= 0:
        raise ValueError("bin_steps must be a positive integer")
    path = Path(comparison_path).resolve()
    result = json.loads(path.read_text(encoding="utf-8"))
    if result["status"] != "completed":
        raise ValueError("Only completed factorial grids can be plotted")
    p = result["protocol"]
    states, rewards = p["states"], p["rewards"]
    label = f"{p['run_type'].upper()} | {len(p['seeds'])} training seeds | reused sources explicitly audited"
    folder = path.parent / "figures"
    folder.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
    x = np.arange(len(rewards))
    for index, state in enumerate(states):
        cells = [result["cells"][f"{state}/{reward}"] for reward in rewards]
        positions = x + (index - 0.5) * 0.32
        ax.bar(positions, [cell["mean_score"] for cell in cells], width=0.3,
               yerr=[cell["std_of_model_mean_scores"] for cell in cells], capsize=4,
               color=COMPARISON_COLORS[index], label=state)
        for position, cell in zip(positions, cells):
            ax.scatter([position] * len(p["seeds"]), cell["per_seed_scores"], color="black", s=18, zorder=3)
    ax.set_xticks(x, rewards)
    ax.set_ylabel("Greedy evaluation mean score")
    ax.set_title(f"{label}\nSD of training-seed means (ddof=0), not confidence intervals")
    ax.legend()
    ax.grid(axis="y", alpha=0.2)
    outputs = [folder / "state_reward_scores.png"]
    fig.savefig(outputs[0], dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    x = np.arange(2)
    for index, state in enumerate(states):
        gains = [result["interactions"][reward][f"{state}_gains"] for reward in rewards[1:]]
        positions = x + (index - 0.5) * 0.32
        axes[0].bar(positions, [np.mean(items) for items in gains], width=0.3,
                    yerr=[np.std(items) for items in gains], capsize=4,
                    color=COMPARISON_COLORS[index], label=state)
        for position, items in zip(positions, gains):
            axes[0].scatter([position] * len(items), items, color="black", s=18, zorder=3)
    items = [result["interactions"][reward] for reward in rewards[1:]]
    axes[1].bar(x, [item["mean_interaction"] for item in items],
                yerr=[item["std_of_paired_interactions"] for item in items],
                color=COMPARISON_COLORS[2:4], capsize=4)
    for position, item in zip(x, items):
        axes[1].scatter([position] * len(p["seeds"]), item["per_seed_interaction"], color="black", s=18, zorder=3)
    for ax in axes:
        ax.set_xticks(x, rewards[1:])
        ax.axhline(0, color="#555555", linewidth=1)
        ax.grid(axis="y", alpha=0.2)
    axes[0].set_ylabel("Shaped score - sparse score (paired seed)")
    axes[1].set_ylabel("Gain(V2) - Gain(V1) (paired seed)")
    axes[0].legend()
    fig.suptitle(f"{label}\nError bars: SD of paired contrasts (ddof=0), not significance tests")
    outputs.append(folder / "interaction_effects.png")
    fig.savefig(outputs[-1], dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained", sharey=True)
    for ax, state in zip(axes, states):
        for reward, color in zip(rewards, COMPARISON_COLORS):
            records = [row for row in result["records"] if row["state_mode"] == state and row["reward_mode"] == reward]
            data = np.array([training_bins(Path(row["checkpoint"]).parent / "metrics.csv",
                                           p["total_steps"], bin_steps, "score") for row in records])
            count = np.sum(np.isfinite(data), axis=0)
            center, spread = np.full(data.shape[1], np.nan), np.full(data.shape[1], np.nan)
            for index in np.flatnonzero(count):
                values = data[:, index][np.isfinite(data[:, index])]
                center[index], spread[index] = np.mean(values), np.std(values)
            x = np.minimum(np.arange(1, len(center) + 1) * bin_steps, p["total_steps"])
            ax.plot(x, center, color=color, label=reward)
            ax.fill_between(x, center - spread, center + spread, where=count == len(records), color=color, alpha=0.15)
        ax.set_title(state)
        ax.set_xlabel("Training environment steps (bin right edge)")
        ax.grid(alpha=0.2)
        ax.legend()
    axes[0].set_ylabel("Training score (with exploration)")
    fig.suptitle(f"{label}\n{bin_steps}-step bins, complete episodes only; no convergence claim")
    outputs.append(folder / "training_scores.png")
    fig.savefig(outputs[-1], dpi=160)
    plt.close(fig)
    return tuple(outputs)


if __name__ == "__main__":
    plot_main(plot_ablation)
