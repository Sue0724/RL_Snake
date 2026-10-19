"""Regenerate V1/V2 training and evaluation plots."""

from experiments.plotting import plot_main, plot_mode_comparison


def plot_state_experiment(comparison_path, *, bin_steps=5000):
    """Plot state modes under the same reward definition."""
    return plot_mode_comparison(comparison_path, mode_field="state_mode", bin_steps=bin_steps)


def main(argv=None):
    plot_main(plot_state_experiment, argv)


if __name__ == "__main__":
    main()
