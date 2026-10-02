"""Fig. grid_visualization: HRTF measurement grid vs. interpolated template.

Source: plotting code originally in 01_interpolation_comparison.ipynb. Needs the current `bayesian_listener` package + the
KEMAR SOFA file -- fast (single-head grid geometry, no fitting).
"""
import numpy as np
import matplotlib.pyplot as plt

from bayesian_listener import BayesianListener
from bayesian_listener.resample import complement_sampling

from . import style
from .style import DEGREE
from notebooks.paths import KEMAR_SOFA

SOFA_PATH = KEMAR_SOFA


def make():
    style.apply_style()

    model = BayesianListener(str(SOFA_PATH))
    model.compute_template(interpolation="SHMAX", use_cache=False)

    orig_coords = model.target.coords
    orig_sph = np.rad2deg(orig_coords.spherical_elevation)  # (az_deg, el_deg, r)
    orig_az_deg, orig_el_deg = orig_sph[:, 0], orig_sph[:, 1]

    pole_mask = (orig_el_deg >= 89.9) & (np.abs(orig_az_deg) > 0.01)
    orig_az_deg = orig_az_deg[~pole_mask]
    orig_el_deg = orig_el_deg[~pole_mask]
    orig_az_deg = (orig_az_deg + 180) % 360 - 180

    template_sph = np.rad2deg(model.template.coords.spherical_elevation)
    template_az_deg = (template_sph[:, 0] + 180) % 360 - 180
    template_el_deg = template_sph[:, 1]

    coords_complemented, complement_mask = complement_sampling(orig_coords)
    comp_sph_el = coords_complemented.spherical_elevation[complement_mask]
    complement_az_deg = (np.rad2deg(comp_sph_el[:, 0]) + 180) % 360 - 180
    complement_el_deg = np.rad2deg(comp_sph_el[:, 1])

    bottom_pole_mask = (complement_el_deg <= -89.9) & (np.abs(complement_az_deg) > 0.01)
    complement_az_deg = complement_az_deg[~bottom_pole_mask]
    complement_el_deg = complement_el_deg[~bottom_pole_mask]

    width_bp = style.COLUMN_WIDTH_BP
    height_bp = width_bp * 0.6
    fig, ax = plt.subplots(figsize=(style.bp_to_in(width_bp), style.bp_to_in(height_bp)))

    color_orig, color_bottom, color_template = "blue", "red", "gray"
    marker_size, alpha = 2, 0.7

    ax.scatter(template_az_deg, template_el_deg, s=marker_size, c=color_template,
               alpha=alpha, edgecolors="none", label="Template")
    ax.scatter(orig_az_deg, orig_el_deg, s=marker_size, c=color_orig,
               alpha=alpha, edgecolors="none", label="Measurement")
    ax.scatter(complement_az_deg, complement_el_deg, s=marker_size + 1, c="none",
               alpha=alpha, edgecolors=color_bottom, linewidths=0.5, label="Complemented")

    ax.set_xlabel(f"Azimuth {DEGREE}")
    ax.set_ylabel(f"Elevation {DEGREE}")
    ax.set_xticks(np.arange(-180, 181, 90))
    ax.set_yticks(np.arange(-90, 91, 45))
    leg = ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02),
                     ncols=3, borderaxespad=0, framealpha=0.8,
                     columnspacing=0.1, handletextpad=0)
    for h in leg.legend_handles:
        h.set_sizes([15])

    fig.tight_layout()
    style.savefig(fig, "grid_visualization", width_bp)
    plt.close(fig)


if __name__ == "__main__":
    make()
