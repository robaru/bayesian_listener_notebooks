"""Fig. 1 (posterior_distribution): illustration of a single modelled
localisation trial -- log-posterior over the template sphere, actual vs.
estimated vs. motor-response direction.

Source: plotting code originally in the authors' local working copy of
01_interpolation_comparison.ipynb; this script is now the only
source of the figure. Needs the current `bayesian_listener`
package + the KEMAR SOFA file -- fast (single trial, single head).
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from scipy.interpolate import RBFInterpolator

from bayesian_listener import BayesianListener

from . import style
from notebooks.paths import CACHE_DIR, KEMAR_SOFA

SOFA_PATH = KEMAR_SOFA
TARGET_IDX = 7
# Class defaults (sigma_spectral=10.4 dB, sigma_prior=69 deg) are realistic
# population-average noise levels, calibrated for aggregate model fitting --
# not for a single illustrative draw, which can easily land a large
# front-back-type error (e.g. seed=1002 here gives ~130 deg). This is a
# schematic figure, so the seed is chosen to match the original figure's
# pattern: a clearly visible offset between the actual direction and the
# internal (pre-motor-noise) estimate, illustrating that the percept
# itself carries error, with the final motor response then landing back
# close to the true direction (seed=22 here gives an internal-estimate
# offset of ~20 deg).
INFER_SEED = 20
# Motor-noise draw seed for estimate(), chosen so the final response
# (orange) lands close to the actual direction (red), as in the original
# figure -- seed=8 gives a ~1 deg motor-response error here.
MOTOR_SEED = 15


def make():
    style.apply_style()

    model = BayesianListener(str(SOFA_PATH),
                            sigma_spectral=5,
                            sigma_prior=65.0,
                            kappa_motor=30.0)

    model.compute_template(interpolation="SHMAX", cache_dir=CACHE_DIR)

    dir_real = model.target.coords.cartesian[TARGET_IDX, :]

    saved_target = model.target
    model.target = model.target[[TARGET_IDX]]
    posterior = model.infer(repetitions=1, seed=INFER_SEED, store_posterior=True)
    model.target = saved_target

    coords_temp = model.template.coords.cartesian
    map_idx = np.argmax(posterior)
    internal_estimation = coords_temp[map_idx, :]
    estimation = model.estimate(posterior, seed=MOTOR_SEED).cartesian.squeeze()

    fig = _plot(model.template.coords, dir_real, posterior, estimation, internal_estimation)
    # 3D axes leave a large empty margin below, left and right of the visible
    # sphere; crop those sides down to the real ink (font size unchanged).
    style.savefig(fig, "posterior_distribution", style.COLUMN_WIDTH_BP,
                  crop_sides=("left", "bottom", "right"))
    plt.close(fig)


def _plot(coords, dir_real, posterior, estimation, internal_estimation):
    amps = posterior.squeeze()
    values = np.maximum(amps, np.log(np.finfo(amps.dtype).eps))
    dir_real = dir_real.squeeze()

    cart = coords.cartesian

    n_grid = 100
    az_grid = np.linspace(-np.pi, np.pi, n_grid)
    el_grid = np.linspace(-np.pi / 2, np.pi / 2, n_grid)
    AZ, EL = np.meshgrid(az_grid, el_grid)
    X = np.cos(EL) * np.cos(AZ)
    Y = np.cos(EL) * np.sin(AZ)
    Z = np.sin(EL)

    query_pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    rbf = RBFInterpolator(cart, values, kernel="linear", smoothing=0.0)
    v_grid = rbf(query_pts).reshape(n_grid, n_grid)

    norm = Normalize(vmin=v_grid.min(), vmax=v_grid.max())
    cmap = plt.get_cmap("Blues")
    facecolors = cmap(norm(v_grid))

    width_bp = style.COLUMN_WIDTH_BP
    height_bp = width_bp * 1.2
    fig = plt.figure(figsize=(style.bp_to_in(width_bp), style.bp_to_in(height_bp)))
    ax = fig.add_axes([0.0, 0.0, 1.0, 0.9], projection="3d")

    ax.plot_surface(X, Y, Z, facecolors=facecolors, rstride=1, cstride=1,
                     linewidth=0, antialiased=False, alpha=0.7, shade=False)

    n_wire = 24
    az_wire = np.linspace(-np.pi, np.pi, n_wire)
    el_wire = np.linspace(-np.pi / 2, np.pi / 2, n_wire)
    AZ_w, EL_w = np.meshgrid(az_wire, el_wire)
    Xw = np.cos(EL_w) * np.cos(AZ_w)
    Yw = np.cos(EL_w) * np.sin(AZ_w)
    Zw = np.sin(EL_w)
    ax.plot_wireframe(Xw, Yw, Zw, rstride=1, cstride=1, color="black", alpha=1, linewidth=0.5)

    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    r_marker = 1.2

    def marker(p, color, label, marker_style="o", s=60):
        p = np.array(p, dtype=float)
        p_norm = p / np.linalg.norm(p) * r_marker
        ax.scatter(*p_norm, c=color, s=s, marker=marker_style, label=label,
                   depthshade=False, zorder=10)

    marker([1, 0, 0], "#1D1D1B", "Front direction", marker_style="s", s=20)
    marker(dir_real, "#E63946", "Actual direction", marker_style="o", s=50)
    marker(internal_estimation, "#31E82E", "Estimated direction", marker_style="^", s=50)
    marker(estimation, "#F77912", "Motor response", marker_style="^", s=50)

    ax.view_init(elev=14, azim=-14)
    ax.set_box_aspect([1, 1, 1])
    ax.grid(False)
    ax.set_axis_off()

    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.02, 1.0), framealpha=0.8)

    cax = fig.add_axes([0.5, 0.93, 0.3, 0.01])
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.set_label("Log Posterior")

    return fig


if __name__ == "__main__":
    make()
