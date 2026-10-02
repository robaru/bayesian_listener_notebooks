"""Regenerate every figure used in the paper.

Run from the repository root with:

    conda activate bayesian_listener_notebooks
    python -m figures.generate_all

Figures that only read pre-computed caches (results/*.csv, results/*.pkl) run in
seconds. Figures that need the `bayesian_listener` package + a SOFA file
(grid_visualization, SH_methods, posterior_distribution, replicate_fig5)
recompute lightweight single-head model geometry -- also fast (no
33-participant fitting or Monte Carlo sweeps are re-run; those results are
only ever read from cache).
"""
import time

from . import fig_parameter_recovery
from . import fig_bic_comparison
from . import fig_metrics_actual_vs_synthetic
from . import fig_nll_stability
from . import fig_grid_visualization
from . import fig_sh_methods
from . import fig_posterior_distribution
from . import fig_replicate5

STEPS = [
    ("supplementary_recovery", fig_parameter_recovery.make),
    ("bic_comparison", fig_bic_comparison.make),
    ("metrics_actual_vs_synthetic", fig_metrics_actual_vs_synthetic.make),
    ("nll_stability_per_trial", fig_nll_stability.make),
    ("grid_visualization", fig_grid_visualization.make),
    ("SH_methods (+ supplementary)", fig_sh_methods.make),
    ("posterior_distribution", fig_posterior_distribution.make),
    ("replicate_fig5_aggregated", fig_replicate5.make),
]


def main():
    for name, fn in STEPS:
        t0 = time.time()
        print(f"=== {name} ===")
        fn()
        print(f"  ({time.time() - t0:.1f}s)")
    print("\nAll figures written to figures/output/. Point widths for LaTeX "
          "\\includegraphics are in figures/output/widths.json.")


if __name__ == "__main__":
    main()
