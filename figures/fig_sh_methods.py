"""Figs. SH_methods / SH_methods_supplementary: spectral-cue colormaps
across interpolation methods, on the median plane.

Source: plotting code originally in 01_interpolation_comparison.ipynb. Needs the current `bayesian_listener` package + the
KEMAR SOFA file -- fast (4 interpolation methods on a single head).
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MaxNLocator
import pyfar as pf

from bayesian_listener import BayesianListener, utils

from . import style
from .style import DEGREE, METHOD_ORDER
from notebooks.paths import CACHE_DIR, KEMAR_SOFA

SOFA_PATH = KEMAR_SOFA
METHODS = METHOD_ORDER #["barumerli2023", "SH", "SHMAX", "barycentric"]


def get_median_plane_spectral(ar, polar_range=(-90, 90), ear=0):
    """Extract spectral cues on the median plane, sorted by polar angle."""
    hpo = np.rad2deg(ar.coords.spherical_side)  # (lateral_deg, polar_deg, r)
    lat, polar = hpo[:, 0], hpo[:, 1]

    median_mask = np.abs(lat) < 1.5
    polar_mask = (polar >= polar_range[0]) & (polar <= polar_range[1])
    mask = median_mask & polar_mask

    polar_sel = polar[mask]
    amps = ar.spectral_cues[mask, :, ear]

    sort_idx = np.argsort(polar_sel)
    return polar_sel[sort_idx], ar.freqs, amps[sort_idx, :]


def _cut_template_grid(target_coords):
    """64-design template grid with the bottom cap removed.

    barumerli2023's order-15 SH interpolation does not extrapolate below the
    lowest measured elevation, so feeding it the full sphere produces
    spurious cues in the unmeasured bottom cap. We reproduce the default
    64-design grid and drop directions below the lowest measured median-plane
    elevation, matching what the AMT model feeds the interpolation.
    """
    dirs = utils.load_n_design(64)  # 2112 quasi-uniform points
    dirs = pf.Coordinates.from_cartesian(dirs[:, 0], dirs[:, 1], dirs[:, 2])
    min_el = np.min(
        target_coords.elevation[np.abs(target_coords.lateral) < 1.5])
    cut = dirs.cartesian[dirs.elevation > min_el, :]
    return pf.Coordinates.from_cartesian(cut[:, 0], cut[:, 1], cut[:, 2])


def _build_models():
    models = {}
    for method in METHODS:
        m = BayesianListener(str(SOFA_PATH))
        if method == "barumerli2023":
            # feed barumerli2023 the reduced grid (no bottom-cap extrapolation)
            m.compute_target(cache_dir=CACHE_DIR)
            grid = _cut_template_grid(m.target.coords)
            m.compute_template(interpolation=method, interpolation_grid=grid,
                               use_cache=False)
        else:
            m.compute_template(interpolation=method, cache_dir=CACHE_DIR)
        models[method] = m
    return models


def make_main(models):
    ear_idx = 0
    ref = models["SHMAX"]

    width_bp = style.COLUMN_WIDTH_BP
    height_bp = width_bp * 1.4
    fig = plt.figure(figsize=(style.bp_to_in(width_bp), style.bp_to_in(height_bp)))
    gs = GridSpec(3, 2, figure=fig, hspace=0.35, wspace=0.15)

    ax_top = fig.add_subplot(gs[0, 0])
    ax_methods = [fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1]),
                  fig.add_subplot(gs[2, 0]), fig.add_subplot(gs[2, 1])]

    def plot_colormap(ax, ar, label, polar_range, show_xlabel, show_ylabel, show_xticks, show_yticks):
        polar, freqs, amps = get_median_plane_spectral(ar, polar_range=polar_range, ear=ear_idx)
        # Per-panel normalisation to the maximum value, as in the source
        # notebook -- this is what "removes" the low-elevation distortion
        # from view in this figure (S1 shows it instead, unnormalised).
        max_val = np.nanmax(amps)
        amps_norm = amps / np.abs(max_val) + 2.0
        im = ax.pcolormesh(freqs, polar, amps_norm, shading="nearest",
                            cmap="RdBu_r", vmin=0.0, vmax=1.0)
        ax.set_xscale("log")
        ax.set_ylim([-90, 90])
        ax.set_title(label, pad=2)
        if show_xlabel:
            ax.set_xlabel("Frequency (Hz)")
        if show_ylabel:
            ax.set_ylabel(f"Elevation {DEGREE}")
        if not show_xticks:
            ax.set_xticklabels([])
        if not show_yticks:
            ax.set_yticklabels([])
        return im

    im = plot_colormap(ax_top, ref.target, "Unprocessed", (-90, 90), False, True, False, True)

    method_configs = [
        ("barumerli2023", (-45, 90), False, True, False, True),
        ("SHMAX", (-90, 90), False, False, False, False),
        ("barycentric", (-90, 90), True, True, True, True),
        ("SH", (-90, 90), True, False, True, False),
    ]

    for ax, (method, polar_range, show_xl, show_yl, show_xt, show_yt) in zip(ax_methods, method_configs):
        plot_colormap(ax, models[method].template, method, polar_range, show_xl, show_yl, show_xt, show_yt)

    fig.canvas.draw()
    pos_left = ax_methods[0].get_position()
    pos_right = ax_methods[1].get_position()
    center_x = (pos_left.x0 + pos_right.x1) / 2
    panel_w, panel_h = pos_left.width, pos_left.height
    ax_top.set_position([center_x - panel_w / 2, ax_top.get_position().y0, panel_w, panel_h])

    fig.canvas.draw()
    pos_br = ax_top.get_position()
    cax = fig.add_axes([pos_br.x1 + 0.02, pos_br.y0, 0.025, pos_br.height])
    cb = fig.colorbar(im, cax=cax, orientation="vertical", label="Normalised\namplitude")
    cb.set_ticks([0.0, 0.5, 1.0])

    style.savefig(fig, "SH_methods", width_bp)
    plt.close(fig)


def make_supplementary(models):
    ear_idx = 0
    model = models["barumerli2023"]  # cut grid (no bottom-cap extrapolation)

    # Full-sphere barumerli2023 for the comparison panel: the default
    # 64-design grid extends below the lowest measured elevation, so the
    # order-15 SH expansion extrapolates into the unmeasured bottom cap and
    # produces the spurious cues shown in the "Full grid" panel -- exactly
    # what feeding the cut grid (top method panel) avoids.
    model_full = BayesianListener(str(SOFA_PATH))
    model_full.compute_template(interpolation="barumerli2023", use_cache=False)

    width_bp = style.COLUMN_WIDTH_BP
    height_bp = width_bp * 2
    fig = plt.figure(figsize=(style.bp_to_in(width_bp), style.bp_to_in(height_bp)))
    # right=0.78 reserves room for the colorbar + its "RMS Amp. (dB)" label
    # within the figure canvas -- otherwise bbox_inches="tight" grows the
    # saved page past the column width to fit them (measured 284bp vs a
    # 246.6bp column budget before this fix).
    gs = GridSpec(3, 1, figure=fig, hspace=0.35, wspace=0.15, left=0.18, right=0.78)

    ax_top = fig.add_subplot(gs[0, 0])
    ax_methods = [fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[2, 0])]

    def plot_colormap(ax, ar, polar_range):
        polar, freqs, amps = get_median_plane_spectral(ar, polar_range=polar_range, ear=ear_idx)
        im = ax.pcolormesh(freqs, polar, amps, shading="nearest", cmap="RdBu_r")
        ax.set_xscale("log")
        ax.set_ylim([-90, 90])
        ax.set_yticks([-45, 0, 45])
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel(f"Elevation {DEGREE}")
        pos = ax.get_position()
        cax = fig.add_axes([pos.x1 + 0.02, pos.y0, 0.025, pos.height])
        cb = fig.colorbar(im, cax, orientation="vertical", label="RMS Amp. (dB)")
        cb.locator = MaxNLocator(nbins=3, integer=True)
        cb.update_ticks()
        return im

    plot_colormap(ax_top, model.target, (-90, 90))
    plot_colormap(ax_methods[0], model.template, (-45, 90))       # cut grid
    plot_colormap(ax_methods[1], model_full.template, (-90, 90))  # full grid

    fig.canvas.draw()

    ax_top.set_title("Unprocessed")
    ax_top.set_xticklabels([])
    ax_top.set_xlabel("")

    ax_methods[0].set_title("barumerli2023")
    ax_methods[0].set_xticklabels([])
    ax_methods[0].set_xlabel("")
    ax_methods[0].plot(ax_methods[0].get_xbound(), (-45, -45), color="#43D757", linewidth=3.0)
    ax_methods[1].plot(ax_methods[1].get_xbound(), (-45, -45), color="#43D757", linewidth=3.0)
    ax_methods[1].set_title("barumerli2023 - Full grid")

    style.savefig(fig, "SH_methods_supplementary", width_bp)
    plt.close(fig)


def make():
    style.apply_style()
    models = _build_models()
    make_main(models)
    make_supplementary(models)


if __name__ == "__main__":
    make()
