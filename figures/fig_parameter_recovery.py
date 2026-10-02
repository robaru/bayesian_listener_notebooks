"""Fig. S3 (supplementary_recovery): parameter recovery scatter plots.

Source: plotting code originally in 04_parameter_recovery.ipynb. Pure pandas/scipy over the cached
results/parameter_recovery_results.csv -- no model computation.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

from . import style
from .style import DEGREE
from notebooks.paths import RESULTS_DIR

PARAMS_TO_EVAL = ["sigma_motor", "sigma_spectral", "sigma_prior"]


def make():
    style.apply_style()
    results_df = pd.read_csv(RESULTS_DIR / "parameter_recovery_results.csv")

    summary = []
    for param in PARAMS_TO_EVAL:
        true_vals = results_df[f"{param}_true"].values
        rec_vals = results_df[f"{param}_recovered"].values
        r, p = stats.pearsonr(true_vals, rec_vals)
        summary.append({"Parameter": param, "r": r})
    summary_df = {row["Parameter"]: row["r"] for row in summary}

    width_bp = style.COLUMN_WIDTH_BP
    height_bp = width_bp * 2
    fig, axes = plt.subplots(3, 1, figsize=(style.bp_to_in(width_bp), style.bp_to_in(height_bp)))

    for ax, param in zip(axes, PARAMS_TO_EVAL):
        true_vals = results_df[f"{param}_true"].values
        rec_vals = results_df[f"{param}_recovered"].values

        ax.scatter(true_vals, rec_vals, s=20, alpha=0.7, edgecolor="black", linewidth=0.5)

        lims = [min(true_vals.min(), rec_vals.min()) * 0.8,
                max(true_vals.max(), rec_vals.max()) * 1.2]
        ax.plot(lims, lims, "k--", lw=1, alpha=0.5)

        slope, intercept = np.polyfit(true_vals, rec_vals, 1)
        x_fit = np.linspace(lims[0], lims[1], 100)
        ax.plot(x_fit, slope * x_fit + intercept, "r-", lw=1, alpha=0.7)

        if param == "sigma_motor":
            paraml, title, xlims = rf"$\sigma_m$ {DEGREE}", "Motor uncertainty", lims
        elif param == "sigma_prior":
            paraml, title, xlims = rf"$\sigma_{{prior}}$ {DEGREE}", "Prior width", [0, 100]
        else:
            paraml, title, xlims = r"$\sigma_{mon}$ (dB)", "Spectral uncertainty", [0, 20]

        ax.set_xlim(xlims)
        ax.set_ylim(lims)
        ax.set_xlabel(f"True {paraml}")
        ax.set_ylabel(f"Recovered {paraml}")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

    fig.tight_layout()
    style.savefig(fig, "supplementary_recovery", width_bp)
    plt.close(fig)


if __name__ == "__main__":
    make()
