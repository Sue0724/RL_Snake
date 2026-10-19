"""Regenerate single-variable comparison plots from raw experiment artifacts."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np


COMPARISON_COLORS = ("#167D8D", "#C24F35", "#7058A3", "#B18A15", "#477BBD", "#9B4D6D")


def training_bins(path, total_steps, bin_steps, metric):
    size = (total_steps + bin_steps - 1) // bin_steps
    values = [[] for _ in range(size)]
    with Path(path).open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["episode_complete"] != "True":
                continue
            step = int(row["global_step"])
            index = (step - 1) // bin_steps
            if 0 <= index < size:
                values[index].append(float(row[metric]))
    return np.array([np.mean(items) if items else np.nan for items in values])


def plot_mode_comparison(comparison_path, *, mode_field, bin_steps=5000):
    if not isinstance(bin_steps, int) or bin_steps <= 0:
        raise ValueError("bin_steps must be a positive integer")
    comparison_path = Path(comparison_path).resolve()
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    if comparison["status"] != "completed":
        raise ValueError("Only completed comparisons can be plotted")
    root = comparison_path.parent
    figures = root / "figures"
    figures.mkdir(exist_ok=True)
    protocol = comparison["protocol"]
    modes_key = f"{mode_field}s"
    modes = protocol[modes_key]
    total_steps = protocol["total_steps"]
    label = f"{protocol['run_type'].upper()} | {len(protocol['seeds'])} training seeds"
    colors = [COMPARISON_COLORS[index % len(COMPARISON_COLORS)] for index in range(len(modes))]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    for mode, color in zip(modes, colors):
        runs = [run for run in comparison["training_runs"] if run[mode_field] == mode]
        for ax, metric in zip(axes, ("score", "episode_return")):
            data = np.array([
                training_bins(root / run["run_dir"] / "metrics.csv", total_steps, bin_steps, metric)
                for run in runs
            ])
            # Empty bins stay empty; never interpolate or treat missing episodes as zero.
            counts = np.sum(np.isfinite(data), axis=0)
            center = np.full(data.shape[1], np.nan)
            spread = np.full_like(center, np.nan)
            for index in np.flatnonzero(counts):
                observations = data[:, index][np.isfinite(data[:, index])]
                center[index] = np.mean(observations)
                spread[index] = np.std(observations)
            x = np.minimum(np.arange(1, len(center) + 1) * bin_steps, total_steps)
            ax.plot(x, center, label=mode, color=color)
            # A band is shown only where every seed supplied a complete episode.
            ax.fill_between(x, center - spread, center + spread,
                            where=counts == len(runs), color=color, alpha=0.15)
            ax.set_xlabel("Training environment steps (bin right edge)")
            ax.grid(alpha=0.2)
    axes[0].set_ylabel("Training score")
    axes[1].set_ylabel("Training return (different reward definitions)" if mode_field == "reward_mode"
                       else "Training return")
    axes[0].legend()
    fig.suptitle(f"{label} | {bin_steps}-step bins | complete episodes only")
    training_path = figures / "training_curves.png"
    fig.savefig(training_path, dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5), layout="constrained")
    summaries = [comparison[modes_key][mode] for mode in modes]
    x = np.arange(len(modes))
    ax.bar(x, [item["mean_score"] for item in summaries],
           yerr=[item["std_of_model_mean_scores"] for item in summaries],
           color=colors[:len(modes)], capsize=5)
    for index, mode in enumerate(modes):
        directory = root / comparison["evaluation_dirs"][mode]
        models = json.loads((directory / "summary.json").read_text(encoding="utf-8"))["models"]
        ax.scatter([index] * len(models), [model["mean_score"] for model in models],
                   color="black", s=20, zorder=3)
    ax.set_xticks(x, modes)
    ax.set_ylabel("Greedy evaluation mean score")
    ax.set_title(f"{label}\nError bars: SD of training-seed means (ddof=0)")
    ax.grid(axis="y", alpha=0.2)
    evaluation_path = figures / "evaluation_scores.png"
    fig.savefig(evaluation_path, dpi=160)
    plt.close(fig)
    return training_path, evaluation_path


def plot_main(plot_function, argv=None):
    parser = argparse.ArgumentParser(description=plot_function.__doc__)
    parser.add_argument("--comparison", required=True)
    parser.add_argument("--bin_steps", type=int, default=5000)
    args = parser.parse_args(argv)
    try:
        for path in plot_function(args.comparison, bin_steps=args.bin_steps):
            print(path)
    except ValueError as error:
        parser.error(str(error))
