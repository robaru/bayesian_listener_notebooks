# Figure generation

These scripts produce every figure of the paper as vector PDFs with a shared
style (`style.py`). They read the cached results in `../results/` (and, for
the model-geometry figures, the KEMAR or ARI SOFA files); they never re-run
the expensive fitting or Monte Carlo analyses, which are done by the
notebooks in `../notebooks/`.

## Running

From the repository root:

```bash
conda activate bayesian_listener_notebooks
python -m figures.generate_all          # all figures
python -m figures.fig_sh_methods        # a single figure
```

The scripts are a Python package (`figures/`) that imports `notebooks/paths.py`,
which is why they are run with `python -m` from the root. Output
goes to `figures/output/<name>.pdf` (git-ignored), together with
`figures/output/widths.json`, the exact post-crop size of every PDF in bp
(1/72 in). In LaTeX, `\includegraphics[width=<width_bp>bp]` reproduces the
figures at 1:1 scale, so the 8 pt font size is the printed size.

`posterior_distribution` is cropped to its visible ink with Ghostscript
(`gs`) plus `pdfcrop` (TeX Live) or, if `pdfcrop` is missing, `pypdf`.

## Figures and inputs

| Paper | Output | Script | Inputs | Model computation |
|---|---|---|---|---|
| Fig. 1 | `posterior_distribution` | `fig_posterior_distribution.py` | KEMAR SOFA | single trial, single head (seconds) |
| Fig. 2 | `grid_visualization` | `fig_grid_visualization.py` | KEMAR SOFA | grid geometry (seconds) |
| Fig. 3 | `SH_methods` | `fig_sh_methods.py` | KEMAR SOFA | 4 interpolations, single head (~30 s) |
| Fig. S1 | `SH_methods_supplementary` | `fig_sh_methods.py` | KEMAR SOFA | (same run) |
| Fig. 4 | `replicate_fig5_aggregated` | `fig_replicate5.py` | `results/replicate_fig5_estimations.pkl` (Git LFS), `results/barumerli2023_fig5.mat`, `data/reference/majdak2010.mat` | none if the cache exists (else 5 ARI subjects from `data/ari/`) |
| Fig. 5 | `metrics_actual_vs_synthetic` | `fig_metrics_actual_vs_synthetic.py` | `results/synthetic_vs_actual_comparison.csv` | none |
| Fig. 6 | `bic_comparison` | `fig_bic_comparison.py` | `results/fitting_results.csv` | none |
| Fig. S2 | `nll_stability_per_trial` | `fig_nll_stability.py` | `results/nll_stability_simulations.pkl` | none |
| Fig. S3 | `supplementary_recovery` | `fig_parameter_recovery.py` | `results/parameter_recovery_results.csv` | none |

KEMAR SOFA = `data/hrtf/KEMAR_FreeFieldCompMinPhase_48kHz.sofa` (tracked in
git); all other inputs are in `results/` or downloaded by `../init.sh`.

## Notes

- The style unifies font size (8 pt), the degree-unit convention `(deg)` and
  the method colours (Okabe-Ito palette) across figures.
- `fig_replicate5.py` uses the shipped estimations cache so that Fig. 4
  reproduces the published numbers exactly; regenerating the cache with
  `bayesian_listener` 0.2.0 shifts them slightly (RNG and motor-noise sampling
  changed). The "grad" variant uses the `barumerli2023pge` convention, which
  is still being finalised in the package
  ([issue #22](https://github.com/robaru/bayesian_listener/issues/22)).
