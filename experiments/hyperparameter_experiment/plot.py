"""Plot exploration comparisons, the schedule and recorded training epsilon."""

import csv
import json
from pathlib import Path

from experiments.plotting import COMPARISON_COLORS, plot_main, plot_mode_comparison


def plot_exploration_experiment(comparison_path, *, bin_steps=5000):
    paths = plot_mode_comparison(comparison_path, mode_field="exploration", bin_steps=bin_steps)
    from matplotlib import pyplot as plt
    import numpy as np

    root = Path(comparison_path).resolve().parent
    comparison = json.loads((root / "comparison.json").read_text(encoding="utf-8"))
    protocol = comparison["protocol"]
    config = protocol["base_config"]
    steps = np.linspace(0, protocol["total_steps"], 1001)
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    for index, (label, decay) in enumerate(zip(protocol["explorations"], protocol["epsilon_decays"])):
        values = np.maximum(config["epsilon_end"], config["epsilon_start"] * decay ** steps)
        line, = ax.plot(steps, values, label=f"decay={decay}",
                        color=COMPARISON_COLORS[index % len(COMPARISON_COLORS)])
        run = next(run for run in comparison["training_runs"] if run["exploration"] == label)
        with (root / run["run_dir"] / "metrics.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        ax.scatter([int(row["global_step"]) for row in rows[::max(1, len(rows) // 30)]],
                   [float(row["epsilon"]) for row in rows[::max(1, len(rows) // 30)]],
                   s=10, color=line.get_color())
    ax.set(xlabel="Completed training environment steps", ylabel="Epsilon",
           title=f"{protocol['run_type'].upper()}: scheduled epsilon; dots = recorded first-seed values")
    ax.legend()
    ax.grid(alpha=0.2)
    path = root / "figures" / "epsilon_schedules.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return (*paths, path)


def main(argv=None):
    plot_main(plot_exploration_experiment, argv)


if __name__ == "__main__":
    main()
