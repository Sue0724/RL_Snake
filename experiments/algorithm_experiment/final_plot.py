"""Plot the frozen candidate, including every training seed on both splits."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np

from experiments.algorithm_experiment.plot import plot_algorithm_experiment
from experiments.plotting import COMPARISON_COLORS, plot_main


def plot_final_experiment(comparison_path, bin_steps=5000):
    outputs = list(plot_algorithm_experiment(comparison_path, bin_steps=bin_steps))
    path = Path(comparison_path).resolve()
    result = json.loads(path.read_text(encoding="utf-8"))
    seeds = result["protocol"]["seeds"]
    fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
    x = np.arange(len(seeds))
    for index, (key, label) in enumerate((("evaluation_dir", "Development"),
                                          ("holdout_evaluation_dir", "Final test"))):
        summary = json.loads((Path(result[key]) / "summary.json").read_text(encoding="utf-8"))
        values = {model["training_seed"]: model["mean_score"] for model in summary["models"]
                  if model["algorithm"] == "dqn"}
        bars = ax.bar(x + (index - 0.5) * 0.36, [values[seed] for seed in seeds], width=0.34,
                      color=COMPARISON_COLORS[index], label=label)
        ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=9)
    ax.set_xticks(x, [str(seed) for seed in seeds])
    ax.set_xlabel("Training seed (not evaluation seed)")
    ax.set_ylabel("Mean score over fixed evaluation episodes")
    ax.set_title("Frozen candidate: all five seeds; no test-based model selection")
    ax.margins(y=0.15)
    ax.grid(axis="y", alpha=0.2)
    ax.legend(loc="lower right")
    destination = path.parent / "figures" / "five_seed_scores.png"
    fig.savefig(destination, dpi=160)
    plt.close(fig)
    return (*outputs, destination)


if __name__ == "__main__":
    plot_main(plot_final_experiment)
