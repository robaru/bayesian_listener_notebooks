"""Fig. replicate_fig5_aggregated: replication of Fig. 5 from Barumerli et
al. (2023), Python vs MATLAB vs measured (Majdak et al. 2010).

Source: 00_replicate_barumerli2023_fig5.ipynb (which also writes the cache below).

The Python points are the *original paper simulations*, read from the
cached (target, estimation) cartesian arrays in
results/replicate_fig5_estimations.pkl (5 ARI subjects, barumerli2023
interpolation, amp + gradient variants; Git LFS). This cache is shipped with
the repo so the figure reproduces the published numbers exactly; recomputing
with the current `bayesian_listener` would shift them (package version +
RNG differences). Also reads data/reference/majdak2010.mat (measured data,
AMT auxdata, downloaded by init.sh) and results/barumerli2023_fig5.mat
(original MATLAB model output).
"""
import numpy as np
import pyfar as pf
from scipy.io import loadmat
from scipy import stats as sp_stats
import matplotlib.pyplot as plt

from bayesian_listener import BayesianListener, metrics, utils

from . import style
from .style import DEGREE
from notebooks.paths import REFERENCE_DIR, RESULTS_DIR, ari_sofa

REPS = 300
BASE_SEED = 42

SIGMA_AMP = {
    "nh12": {"sigma_itd": 0.569, "sigma_ild": 0.5, "sigma_spectral": 3.4, "sigma_prior": 11.5, "kappa_motor": 1.0 / (np.deg2rad(8.5) ** 2)},
    "nh15": {"sigma_itd": 0.569, "sigma_ild": 0.5, "sigma_spectral": 3.2, "sigma_prior": 10.0, "kappa_motor": 1.0 / (np.deg2rad(14.27) ** 2)},
    "nh16": {"sigma_itd": 0.569, "sigma_ild": 1.0, "sigma_spectral": 3.6, "sigma_prior": 11.5, "kappa_motor": 1.0 / (np.deg2rad(11.0) ** 2)},
    "nh17": {"sigma_itd": 0.569, "sigma_ild": 0.5, "sigma_spectral": 4.1, "sigma_prior": 11.5, "kappa_motor": 1.0 / (np.deg2rad(14.3) ** 2)},
    "nh18": {"sigma_itd": 0.569, "sigma_ild": 1.0, "sigma_spectral": 6.5, "sigma_prior": 11.5, "kappa_motor": 1.0 / (np.deg2rad(14.0) ** 2)},
}
SIGMA_GRAD = {
    "nh12": {"sigma_itd": 0.569, "sigma_ild": 0.5, "sigma_spectral": 1.1, "sigma_prior": 11.5, "kappa_motor": 1.0 / (np.deg2rad(8.5) ** 2)},
    "nh15": {"sigma_itd": 0.569, "sigma_ild": 0.5, "sigma_spectral": 1.25, "sigma_prior": 11.0, "kappa_motor": 1.0 / (np.deg2rad(14.3) ** 2)},
    "nh16": {"sigma_itd": 0.569, "sigma_ild": 1.0, "sigma_spectral": 1.25, "sigma_prior": 11.5, "kappa_motor": 1.0 / (np.deg2rad(11.5) ** 2)},
    "nh17": {"sigma_itd": 0.569, "sigma_ild": 1.0, "sigma_spectral": 1.6, "sigma_prior": 11.5, "kappa_motor": 1.0 / (np.deg2rad(14.0) ** 2)},
    "nh18": {"sigma_itd": 0.569, "sigma_ild": 1.0, "sigma_spectral": 2.1, "sigma_prior": 11.5, "kappa_motor": 1.0 / (np.deg2rad(15.0) ** 2)},
}
SOFA_FILE = {key: ari_sofa(key) for key in SIGMA_AMP}

METRICS_TO_COMPUTE = ["rmsL", "rmsPmedianlocal", "querrMiddlebrooks"]
LATITUDE_BOUNDARIES = np.deg2rad([-90, -30, 30, 90])
LATITUDE_LABELS = [-60, 0, 60]
POLAR_BOUNDARIES = np.deg2rad([-30, 30, 150, 210])
POLAR_LABELS = [0, 90, 180]
SECTOR_POSITIONS = {
    "rmsL": LATITUDE_LABELS,
    "rmsPmedianlocal": POLAR_LABELS,
    "querrMiddlebrooks": POLAR_LABELS,
}
METRIC_TITLES = [f"Lateral\nerror {DEGREE}", f"Polar\nerror {DEGREE}", "Quadrant\nerror (%)"]
Y_LIMITS = [(0, 20), (0, 60), (-5, 40)]


def _sector_metrics(true_hp, est_hp):
    """Compute METRICS_TO_COMPUTE by spatial sector from raw (lat, pol) arrays."""
    out = {}
    for metric in METRICS_TO_COMPUTE:
        if metric == "rmsL":
            bounds, labels, angle_true = LATITUDE_BOUNDARIES, LATITUDE_LABELS, true_hp[:, 0]
        else:
            bounds, labels, angle_true = POLAR_BOUNDARIES, POLAR_LABELS, true_hp[:, 1]

        out[metric] = {}
        for i, label in enumerate(labels):
            mask = (angle_true >= bounds[i]) & (angle_true < bounds[i + 1])
            if not np.any(mask):
                out[metric][label] = {"value": np.nan}
                continue
            metric_func = metrics.METRIC_FUNCTIONS[metric]
            value, _ = metric_func(true_hp[mask], est_hp[mask])
            unit = metric_func._metadata["output_unit"]
            out[metric][label] = {"value": np.rad2deg(value) if unit == "radians" else value}
    return out


CONVENTION = {"amp": "Barumerli2023", "grad": "barumerli2023pge"}

# Cache raw numpy arrays only (not BayesianListener/pf.Coordinates objects) --
# the originally-shipped model/estimation pickles broke across a
# bayesian_listener refactor because they pickled package-internal classes;
# plain arrays keyed by (variant, subject) survive package changes.
ESTIMATIONS_CACHE = RESULTS_DIR / "replicate_fig5_estimations.pkl"


def _cut_template_grid(target_coords):
    """64-design template grid with the bottom cap removed.

    barumerli2023's order-15 SH interpolation does not extrapolate below the
    lowest measured elevation, so feeding it the full sphere produces
    spurious cues in the unmeasured bottom cap. We reproduce the default
    64-design grid and drop directions below the lowest measured median-plane
    elevation, matching what the AMT model feeds the interpolation (same cut
    as fig_sh_methods.py).
    """
    dirs = utils.load_n_design(64)  # 2112 quasi-uniform points
    dirs = pf.Coordinates.from_cartesian(dirs[:, 0], dirs[:, 1], dirs[:, 2])
    min_el = np.min(
        target_coords.elevation)
    cut = dirs.cartesian[dirs.elevation > min_el, :]
    return pf.Coordinates.from_cartesian(cut[:, 0], cut[:, 1], cut[:, 2])


def _compute_raw(variant, sbj, params):
    m = BayesianListener(str(SOFA_FILE[sbj]), **params)
    m.compute_target(convention=CONVENTION[variant], use_cache=False)
    # feed barumerli2023 the reduced grid (no bottom-cap extrapolation)
    grid = _cut_template_grid(m.target.coords)
    m.compute_template(interpolation="barumerli2023", interpolation_grid=grid,
                       use_cache=False)

    posterior = m.infer(repetitions=REPS, seed=BASE_SEED)
    estimations = m.estimate(posterior, seed=BASE_SEED)
    return m.coords.cartesian, estimations.cartesian.reshape(-1, 3)


def _load_computed_metrics():
    import pickle
    import time

    subjects = list(SIGMA_AMP.keys())
    sigma_maps = {"amp": SIGMA_AMP, "grad": SIGMA_GRAD}

    if ESTIMATIONS_CACHE.exists():
        print(f"  loading cached model estimations from {ESTIMATIONS_CACHE.name}")
        with open(ESTIMATIONS_CACHE, "rb") as f:
            raw = pickle.load(f)
    else:
        raw = {}
        for variant in ["amp", "grad"]:
            for sbj in subjects:
                t0 = time.time()
                raw[(variant, sbj)] = _compute_raw(variant, sbj, sigma_maps[variant][sbj])
                print(f"  {variant}/{sbj}: {time.time() - t0:.1f}s")
        with open(ESTIMATIONS_CACHE, "wb") as f:
            pickle.dump(raw, f)

    estims = {"amp": {}, "grad": {}}
    targets = {"amp": {}, "grad": {}}
    for variant in ["amp", "grad"]:
        for sbj in subjects:
            model_coords, estims_flat = raw[(variant, sbj)]
            estims[variant][sbj] = pf.Coordinates.from_cartesian(
                estims_flat[:, 0], estims_flat[:, 1], estims_flat[:, 2])

            targets_repeated = np.repeat(model_coords, REPS, axis=0)
            targets[variant][sbj] = pf.Coordinates.from_cartesian(
                targets_repeated[:, 0], targets_repeated[:, 1], targets_repeated[:, 2])

    computed_metrics = {"amp": {}, "grad": {}}
    for variant in ["amp", "grad"]:
        for sbj in subjects:
            true_hp = targets[variant][sbj].spherical_side
            est_hp = estims[variant][sbj].spherical_side
            computed_metrics[variant][sbj] = _sector_metrics(true_hp, est_hp)

    return subjects, computed_metrics


def _load_measured_metrics(subjects):
    mat_data = loadmat(REFERENCE_DIR / "majdak2010.mat", struct_as_record=False, squeeze_me=True)
    subjects_mat = mat_data["subject"]
    condition_index = 4  # Free-field condition

    measured_metrics = {}
    for subj_struct in subjects_mat:
        id_mat = subj_struct.id.lower()
        if id_mat not in subjects:
            continue

        exp = getattr(subj_struct, "expData")[condition_index].real
        if exp.ndim == 1:
            exp = exp.reshape(-1, 9)

        # exp columns 0:2 / 2:4 are (azimuth, elevation) in degrees, not
        # already (lateral, polar) -- convert via pf.Coordinates like the
        # source notebook, then read off the horizontal-polar convention
        # _sector_metrics expects (matching _load_computed_metrics, which
        # gets its (lateral, polar, r) triples the same way).
        true_arr = np.hstack([np.deg2rad(exp[:, 0:2]), np.ones((exp.shape[0], 1))])
        est_arr = np.hstack([np.deg2rad(exp[:, 2:4]), np.ones((exp.shape[0], 1))])
        true_hp = pf.Coordinates.from_spherical_elevation(
            true_arr[:, 0], true_arr[:, 1], true_arr[:, 2]).spherical_side
        est_hp = pf.Coordinates.from_spherical_elevation(
            est_arr[:, 0], est_arr[:, 1], est_arr[:, 2]).spherical_side
        measured_metrics[id_mat] = _sector_metrics(true_hp, est_hp)

    return measured_metrics


def _load_matlab_metrics(subjects):
    mat_file = loadmat(RESULTS_DIR / "barumerli2023_fig5.mat", struct_as_record=False, squeeze_me=True)
    fig5 = mat_file["cache"].value  # 5x2 array of Nx8 matrices (degrees)
    variants_map = {0: "amp", 1: "grad"}

    matlab_metrics = {variant: {} for variant in ["amp", "grad"]}
    for s_idx, sbj in enumerate(subjects):
        for v_idx, variant in variants_map.items():
            data_mat = fig5[s_idx, v_idx]
            # Columns 4:6 / 6:8 of the MATLAB cache are already (lateral,
            # polar) in degrees (unlike the measured data above) -- just
            # append a unit radius column to match the (lat, pol, r)
            # convention _sector_metrics expects.
            true_hp = np.column_stack([np.deg2rad(data_mat[:, 4]), np.deg2rad(data_mat[:, 5]),
                                       np.ones(len(data_mat))])
            est_hp = np.column_stack([np.deg2rad(data_mat[:, 6]), np.deg2rad(data_mat[:, 7]),
                                      np.ones(len(data_mat))])
            matlab_metrics[variant][sbj] = _sector_metrics(true_hp, est_hp)

    return matlab_metrics


def _collect_values(source_dict, variant, metric, x_vals, subjects_order):
    return np.array([
        [source_dict[variant][sbj][metric].get(x, {}).get("value", np.nan) for x in x_vals]
        for sbj in subjects_order
    ])


def make():
    style.apply_style()

    subjects, computed_metrics = _load_computed_metrics()
    measured_metrics = _load_measured_metrics(subjects)
    matlab_metrics = _load_matlab_metrics(subjects)

    width_bp = style.COLUMN_WIDTH_BP * 2 * 0.4
    height_bp = style.COLUMN_WIDTH_BP * 2 * 0.6
    fig, axes = plt.subplots(3, 1, figsize=(style.bp_to_in(width_bp), style.bp_to_in(height_bp)))

    def plot_mean_se(ax, x_vals, data, marker, color, label, filled):
        mean = np.nanmean(data, axis=0)
        se = sp_stats.sem(data, axis=0, nan_policy="omit")
        fc = color if filled else "none"
        ax.errorbar(x_vals, mean, yerr=se, fmt=marker, color=color,
                     markerfacecolor=fc, markeredgecolor=color,
                     capsize=3, markersize=3, label=label)

    for row, metric in enumerate(METRICS_TO_COMPUTE):
        ax = axes[row]
        x_vals = np.array(SECTOR_POSITIONS[metric])

        meas = np.array([[measured_metrics[sbj][metric].get(x, {}).get("value", np.nan)
                          for x in x_vals] for sbj in subjects])
        py_amp = _collect_values(computed_metrics, "amp", metric, x_vals, subjects)
        py_grad = _collect_values(computed_metrics, "grad", metric, x_vals, subjects)
        ml_amp = _collect_values(matlab_metrics, "amp", metric, x_vals, subjects)
        ml_grad = _collect_values(matlab_metrics, "grad", metric, x_vals, subjects)

        dodge = 0.07 * (x_vals.max() - x_vals.min())
        plot_mean_se(ax, x_vals, meas, "o", "grey", "Measured", filled=True)
        plot_mean_se(ax, x_vals - 2 * dodge, py_amp, "s", "red", "Python amp", filled=False)
        plot_mean_se(ax, x_vals - dodge, ml_amp, "s", "black", "MATLAB amp", filled=False)
        plot_mean_se(ax, x_vals + dodge, py_grad, "^", "red", "Python grad", filled=False)
        plot_mean_se(ax, x_vals + 2 * dodge, ml_grad, "^", "black", "MATLAB grad", filled=False)

        ax.set_ylabel(METRIC_TITLES[row])
        ax.set_ylim(Y_LIMITS[row])
        ax.set_xticks(x_vals)
        ax.grid(True, alpha=0.3)

        if row == 1:
            ax.set_xticklabels([])
            ax.set_yticks([0, 30, 60])

    axes[0].set_xlabel(f"Lateral angle {DEGREE}")
    axes[2].set_xlabel(f"Polar angle {DEGREE}")

    # Factored legend matching the original figure: colour (Measured/
    # Python/MATLAB) and marker shape (grad=triangle/amp=square) are
    # explained as separate proxy entries rather than 5 full colour+shape
    # combinations. matplotlib's legend fills column-major (not row-major),
    # so with ncol=3 the handles below (an invisible spacer under Measured
    # gives column sizes [2, 2, 2]) read left-to-right, top-to-bottom as
    #   [Measured, Python, grad] / [(blank), MATLAB, amp]
    # i.e. the middle column groups the two implementations (Python/MATLAB)
    # and the right column the two variants (grad/amp), matching the figure.
    from matplotlib.lines import Line2D
    blank = Line2D([0], [0], marker="None", linestyle="None", label="")
    legend_handles = [
        Line2D([0], [0], marker="o", linestyle="None", markerfacecolor="grey",
               markeredgecolor="grey", label="Measured"),
        blank,
        Line2D([0], [0], marker="o", linestyle="None", markerfacecolor="red",
               markeredgecolor="red", label="Python"),
        Line2D([0], [0], marker="o", linestyle="None", markerfacecolor="black",
               markeredgecolor="black", label="MATLAB"),
        Line2D([0], [0], marker="^", linestyle="None", markerfacecolor="black",
               markeredgecolor="black", label="grad"),
        Line2D([0], [0], marker="s", linestyle="None", markerfacecolor="black",
               markeredgecolor="black", label="amp"),
    ]
    fig.legend(handles=legend_handles, loc="upper center", ncol=3,
               bbox_to_anchor=(0.5, 1.0), frameon=False, columnspacing=1.0, handletextpad=0.3)
    # rect reserves the top for the legend above -- tight_layout() only
    # sizes around axes content, not an external fig.legend(), so without
    # this the legend overlapped the top panel.
    fig.tight_layout(rect=[0, 0, 1, 0.88])
    style.savefig(fig, "replicate_fig5_aggregated", width_bp)
    plt.close(fig)


if __name__ == "__main__":
    make()
