"""Regenerate reward experiment plots from comparison.json and raw CSV logs."""

from experiments.plotting import plot_main, plot_mode_comparison, training_bins


def plot_reward_experiment(comparison_path, *, bin_steps=5000):
    """Plot reward modes; preserve the existing public plotting API."""
    return plot_mode_comparison(comparison_path, mode_field="reward_mode", bin_steps=bin_steps)


def main(argv=None):
    plot_main(plot_reward_experiment, argv)


if __name__ == "__main__":
    main()
