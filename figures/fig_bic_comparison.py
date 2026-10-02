"""Fig. bic_comparison: mean +/- SE delta-BIC per interpolation method.

Source: plotting code originally in 08_posterior_predictive_checks.ipynb. Pure pandas over the cached
results/fitting_results.csv -- no model computation.
`n_trials` in that CSV is the same per-participant trial count the
notebook's `n_obs` fallback would have recomputed from the (external,
not-copied-in) AXD dataset, so it's used directly here.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from . import style
from .style import METHOD_COLORS, METHOD_ORDER
from notebooks.paths import FITTING_RESULTS

METHODS = METHOD_ORDER
K_PARAMS = 3


def make():
    style.apply_style()
    fitted_params_df = pd.read_csv(FITTING_RESULTS)
    fitted_params_df = fitted_params_df[fitted_params_df["success"] == True]  # noqa: E712

    fitted_params_df["BIC"] = (K_PARAMS * np.log(fitted_params_df["n_trials"])
                                + 2 * fitted_params_df["nll_500"])

    bic_rows = []
    for pid in fitted_params_df["participant"].unique():
        p_data = fitted_params_df[fitted_params_df["participant"] == pid]
        min_bic = p_data["BIC"].min()
        for _, row in p_data.iterrows():
            bic_rows.append({"participant": pid, "method": row["method"],
                              "delta_bic": row["BIC"] - min_bic})
    bic_df = pd.DataFrame(bic_rows)

    stats_rows = []
    for method in METHODS:
        data = bic_df[bic_df["method"] == method]["delta_bic"].values
        stats_rows.append({"method": method, "mean": np.mean(data),
                            "se": np.std(data) / np.sqrt(len(data))})
    stats_df = pd.DataFrame(stats_rows)

    width_bp = style.COLUMN_WIDTH_BP
    height_bp = width_bp / 1.6
    fig, ax = plt.subplots(figsize=(style.bp_to_in(width_bp), style.bp_to_in(height_bp)))

    for i, row in stats_df.iterrows():
        ax.errorbar(i, row["mean"], yerr=row["se"], fmt="o", markersize=5,
                     color=METHOD_COLORS[row["method"]], elinewidth=1.2, capsize=4, capthick=1.2)

    ax.set_xlim([-0.7, len(stats_df) - 0.3])
    ax.set_xticks(range(len(stats_df)))
    ax.set_xticklabels(stats_df["method"])
    ax.set_ylabel(r"$\Delta$BIC (vs. best model)")
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(width=0.8, length=4)

    fig.tight_layout()
    style.savefig(fig, "bic_comparison", width_bp)
    plt.close(fig)


if __name__ == "__main__":
    make()
