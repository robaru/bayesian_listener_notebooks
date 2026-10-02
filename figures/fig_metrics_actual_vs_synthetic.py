"""Fig. metrics_actual_vs_synthetic: posterior predictive checks (2x2 grid).

Source: plotting code originally in 08_posterior_predictive_checks.ipynb. `results/synthetic_vs_actual_comparison.csv` already
contains the merged actual+synthetic metrics table (`metrics_df` in the
notebook) -- no model computation needed.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats as sp_stats

from . import style
from .style import DEGREE, METHOD_COLORS, METHOD_ORDER
from notebooks.paths import RESULTS_DIR


METRICS_TO_PLOT = [
    ("rmsL_deg", f"LE {DEGREE}"),
    ("rmsPmedianlocal_deg", f"PE {DEGREE}"),
    ("querrMiddlebrooks", "QE (%)"),
]


def make():
    style.apply_style()
    metrics_df = pd.read_csv(RESULTS_DIR / "synthetic_vs_actual_comparison.csv")
    actual_df = metrics_df[metrics_df["data_type"] == "actual"].copy()
    synth_df = metrics_df[metrics_df["data_type"] == "synthetic"].copy()
    participants = actual_df["participant"].unique()

    width_bp = style.COLUMN_WIDTH_BP
    height_bp = width_bp
    fig, axes = plt.subplots(2, 2, figsize=(style.bp_to_in(width_bp), style.bp_to_in(height_bp)))
    fig.patch.set_facecolor("white")

    ax_positions = [axes[0, 0], axes[1, 0], axes[1, 1]]
    ax_legend = axes[0, 1]

    legend_handles, legend_labels = [], []

    for ax, (metric, ylabel) in zip(ax_positions, METRICS_TO_PLOT):
        actual_vals_all, synth_vals_all = [], []
        for method in METHOD_ORDER:
            for participant in participants:
                a = actual_df[actual_df["participant"] == participant][metric].values[0]
                s_data = synth_df[(synth_df["participant"] == participant) &
                                   (synth_df["method"] == method)]
                if len(s_data) > 0:
                    actual_vals_all.append(a)
                    synth_vals_all.append(s_data[metric].values[0])

        all_vals = actual_vals_all + synth_vals_all
        ax_min, ax_max = min(all_vals), max(all_vals)
        pad = (ax_max - ax_min) * 0.05
        ax_min -= pad
        ax_max += pad

        handles = []
        for method in METHOD_ORDER:
            color = METHOD_COLORS[method]
            actual_vals, synth_vals = [], []
            for participant in participants:
                a = actual_df[actual_df["participant"] == participant][metric].values[0]
                s_data = synth_df[(synth_df["participant"] == participant) &
                                   (synth_df["method"] == method)]
                if len(s_data) > 0:
                    actual_vals.append(a)
                    synth_vals.append(s_data[metric].values[0])

            actual_vals = np.array(actual_vals)
            synth_vals = np.array(synth_vals)

            slope, intercept, r, p, se = sp_stats.linregress(actual_vals, synth_vals)
            x_range = np.linspace(ax_min, ax_max, 50)
            y_pred = slope * x_range + intercept

            n = len(actual_vals)
            t_crit = sp_stats.t.ppf(0.975, df=n - 2)
            x_mean = actual_vals.mean()
            ss_x = np.sum((actual_vals - x_mean) ** 2)
            resid = synth_vals - (slope * actual_vals + intercept)
            s_err = np.sqrt(np.sum(resid ** 2) / (n - 2))
            ci = t_crit * s_err * np.sqrt(1 / n + (x_range - x_mean) ** 2 / ss_x)

            ax.fill_between(x_range, y_pred - ci, y_pred + ci, color=color, alpha=0.1)
            line, = ax.plot(x_range, y_pred, color=color, linewidth=1, label=method)
            handles.append(line)

        if metric == "rmsPmedianlocal_deg":
            ax.set_xticks((20, 30, 40))
        ax.plot([ax_min, ax_max], [ax_min, ax_max], "k--", alpha=0.3, linewidth=0.9)

        ax.set_xlim(ax_min, ax_max)
        ax.set_ylim(ax_min, ax_max)
        ax.set_xlabel("Actual " + ylabel)
        ax.set_ylabel("Simulated " + ylabel)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_aspect("equal", adjustable="box")

        if metric == "querrMiddlebrooks":
            ax.set_yticks((0,20,40))

        if not legend_handles:
            legend_handles = handles
            legend_labels = METHOD_ORDER

    ax_legend.set_axis_off()
    ax_legend.legend(handles=legend_handles, labels=legend_labels, frameon=False,
                      loc="center", ncol=1)

    fig.tight_layout()
    style.savefig(fig, "metrics_actual_vs_synthetic", width_bp)
    plt.close(fig)


if __name__ == "__main__":
    make()
