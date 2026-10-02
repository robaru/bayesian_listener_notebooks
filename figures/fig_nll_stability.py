"""Fig. S2 (nll_stability_per_trial): NLL estimation stability vs MC samples.

Source: plotting code originally in 03_nll_stability.ipynb, reading results/nll_stability_simulations.pkl -- no model
computation.

Note: the notebook's "Compute statistics" cell (which builds
`std_per_trial_mean`/`std_per_trial_sd` from `nll_results`) was lost at
some point and has been restored in the notebook from this script. The
computation below was reconstructed to match the plotting cell's variable
names/semantics and was checked numerically against the y-values in the
currently-published figure (nll_stability_per_trial.eps):
per parameter set, the NLL standard deviation across bootstrap replicates
(a standard-error-like quantity by construction) is divided by
sqrt(n_observed_trials) -- i.e. the CLT-scaled per-trial NLL uncertainty
-- then averaged (and the SE derived) across the 28 parameter sets.
"""
import pickle
import numpy as np
import matplotlib.pyplot as plt

from . import style
from notebooks.paths import RESULTS_DIR



def make():
    style.apply_style()
    with open(RESULTS_DIR / "nll_stability_simulations.pkl", "rb") as f:
        cached = pickle.load(f)

    nll_results = cached["nll_results"]  # (n_params, n_reps, n_mc, N_BOOTSTRAP)
    REPS_PER_TARGET = cached["REPS_PER_TARGET"]
    MC_SAMPLES_LIST = cached["MC_SAMPLES_LIST"]
    TARGET_GRID = cached["TARGET_GRID"]
    n_targets = len(TARGET_GRID)
    n_params = nll_results.shape[0]

    n_obs_per_rep = np.array(REPS_PER_TARGET) * n_targets  # (n_reps,)
    std_per_trial = nll_results.std(axis=3) / np.sqrt(n_obs_per_rep)[None, :, None]  # (n_params, n_reps, n_mc)
    std_per_trial_mean = std_per_trial.mean(axis=0)  # (n_reps, n_mc)
    std_per_trial_sd = std_per_trial.std(axis=0)      # (n_reps, n_mc)

    width_bp = style.COLUMN_WIDTH_BP
    height_bp = width_bp / 1.6
    fig, ax = plt.subplots(figsize=(style.bp_to_in(width_bp), style.bp_to_in(height_bp)))

    markers = ["o", "s", "^"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    dodge = [-8, 0, 8]
    for i, reps in enumerate(REPS_PER_TARGET):
        n_obs = reps * n_targets
        label = f"{reps} reps/dir ({n_obs} trials)"
        x_dodged = np.array(MC_SAMPLES_LIST) + dodge[i]
        ax.errorbar(
            x_dodged, std_per_trial_mean[i, :],
            yerr=std_per_trial_sd[i, :] / np.sqrt(n_params),
            fmt=f"{markers[i]}-", color=colors[i], label=label,
            lw=0.8, markersize=3, capsize=2, capthick=0.6,
        )

    ax.axvline(x=200, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.set_xlabel("Monte Carlo samples")
    ax.set_ylabel("Per-trial NLL SD")
    ax.legend(loc="upper right")
    ax.set_xlim([25, 525])
    ax.set_ylim([0, None])

    fig.tight_layout()
    style.savefig(fig, "nll_stability_per_trial", width_bp)
    plt.close(fig)


if __name__ == "__main__":
    make()
