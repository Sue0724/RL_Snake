"""Plot algorithm comparisons from raw logs and greedy evaluations."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np

from experiments.plotting import COMPARISON_COLORS, plot_main, training_bins


def plot_algorithm_experiment(comparison_path, bin_steps=5000):
    if type(bin_steps) is not int or bin_steps <= 0:
        raise ValueError("bin_steps must be a positive integer")
    path = Path(comparison_path).resolve()
    result = json.loads(path.read_text(encoding="utf-8"))
    if result["status"] != "completed":
        raise ValueError("Only completed experiments can be plotted")
    protocol = result["protocol"]
    algorithms = protocol["algorithms"]
    folder = path.parent / "figures"
    folder.mkdir(exist_ok=True)
    label = f"{protocol['run_type'].upper()} | {len(protocol['seeds'])} training seeds"
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    for algorithm, color in zip(algorithms, COMPARISON_COLORS):
        runs = [run for run in result["training_runs"] if run["algorithm"] == algorithm]
        for ax, metric in zip(axes, ("score", "episode_return")):
            values = np.array([training_bins(path.parent / run["run_dir"] / "metrics.csv",
                                            protocol["total_steps"], bin_steps, metric) for run in runs])
            counts = np.sum(np.isfinite(values), axis=0)
            center = np.full(values.shape[1], np.nan)
            spread = np.full_like(center, np.nan)
            for index in np.flatnonzero(counts):
                items = values[:, index][np.isfinite(values[:, index])]
                center[index], spread[index] = np.mean(items), np.std(items)
            x = np.minimum(np.arange(1, len(center) + 1) * bin_steps, protocol["total_steps"])
            ax.plot(x, center, label=algorithm, color=color)
            ax.fill_between(x, center - spread, center + spread, where=counts == len(runs),
                            color=color, alpha=0.15)
            ax.set_xlabel("Training environment steps (bin right edge)")
            ax.grid(alpha=0.2)
    axes[0].set_ylabel("Training score")
    axes[1].set_ylabel("Training return")
    axes[0].legend()
    fig.suptitle(f"{label} | {bin_steps}-step bins | complete episodes only")
    outputs = [folder / "training_curves.png"]
    fig.savefig(outputs[0], dpi=160)
    plt.close(fig)

    for split, key in (("development", "evaluation_dir"), ("holdout", "holdout_evaluation_dir")):
        if key not in result:
            continue
        summary = json.loads((path.parent / result[key] / "summary.json").read_text(encoding="utf-8"))
        names = algorithms + ["random"]
        groups = [[model["mean_score"] for model in summary["models"] if model["algorithm"] == name]
                  for name in names]
        fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
        ax.bar(range(len(names)), [np.mean(items) for items in groups],
               yerr=[np.std(items) if len(items) > 1 else 0 for items in groups],
               color=list(COMPARISON_COLORS[:len(algorithms)]) + ["#777777"], capsize=5)
        for index, items in enumerate(groups):
            ax.scatter([index] * len(items), items, color="black", s=20, zorder=3)
        ax.set_xticks(range(len(names)), names)
        ax.set_ylabel("Greedy evaluation mean score")
        ax.set_title(f"{label} | {split}\nSD of training-seed means (ddof=0); Random = one policy")
        ax.grid(axis="y", alpha=0.2)
        destination = folder / f"{split}_scores.png"
        fig.savefig(destination, dpi=160)
        plt.close(fig)
        outputs.append(destination)
    return tuple(outputs)


if __name__ == "__main__":
    plot_main(plot_algorithm_experiment)
