# Bayesian Listener — Analysis Notebooks

Notebooks, figure scripts and cached results for

> R. Barumerli, F. Brinkmann, E. Zanoni, A. Hoyer, L. Picinali, and M. Geronazzo,
> "Statistical validation and full-sphere extension of a Bayesian model for human static
> sound localisation," *Acta Acustica* **10**, 89 (2026).
> [doi:10.1051/aacus/2026084](https://doi.org/10.1051/aacus/2026084)

The model itself is the Python package [`bayesian_listener`](https://github.com/robaru/bayesian_listener).

## Quick start

```bash
git lfs install
git clone https://github.com/robaru/bayesian_listener_notebooks.git
cd bayesian_listener_notebooks
./init.sh                              # conda env, Jupyter kernel, data downloads
conda activate bayesian_listener_notebooks
python -m figures.generate_all         # all paper figures -> figures/output/
jupyter lab
```

Figures, notebook `09` and the R analysis run in seconds from the cached results in `results/`.

## Repository layout

| Folder | Content |
|---|---|
| [`notebooks/`](notebooks/) | analysis notebooks, one per paper section ([list](notebooks/README.md)) |
| [`figures/`](figures/) | one script per paper figure ([list](figures/README.md)) |
| [`stats/`](stats/) | statistical tests and model comparison (Sec. 3.4–3.5) |
| [`results/`](results/) | cached results read by the figures, `stats/` and notebook `09` |
| [`scripts/`](scripts/) | HRTF download script used by `init.sh` |
| `data/` | downloaded inputs (git-ignored); set `BL_DATA_DIR` to keep them elsewhere |

## Notes on the published values

`09_verify_reported_statistics` reproduces all values in the paper. A few reporting details
differ; none changes a conclusion:

- Sec. 3.2 and 3.3: the "± standard error" values for the template RMSE and the per-trial NLL are
  standard deviations.
- Sec. 3.3: the recovery of the lateral error is r = 0.97 (paper: 0.96).
- Sec. 3.4.1: "Wilcoxon p > .27" holds for SHMAX; over all methods the smallest p is .13.
- Table 2: "Wins" counts participants with ΔBIC < −2, not merely a lower BIC.

The paper was computed with a development version of `bayesian_listener` (commit `c0b711a`). The
released package now computes the spectral features much faster, at a different absolute level. This
only affects the `barumerli2023` interpolation, which regularises the order-0 SH coefficient (unlike
the original MATLAB implementation) and therefore depends on the feature level: re-running it gives
slightly different values. The cached results in `results/` are the paper's.

## Data

- HRTFs: [SONICOM HRTF dataset](https://doi.org/10.17605/OSF.IO/XRZ8J) (Engel et al., 2023). The
  KEMAR HRTF is included (CC BY-SA 3.0); participant HRTFs are downloaded by `init.sh`.
- Behavioural data: Poole et al. (2026), [SONICOM Ecosystem database #58](https://ecosystem.sonicom.eu/databases/58),
  doi:10.60887/xgb6m7bcyg4c1nv1, downloaded by `init.sh`.
- Fig. 4: ARI HRTFs and data of Majdak et al. (2010) from the
  [Auditory Modeling Toolbox](https://sofacoustics.org/data/amt-1.0.0/), downloaded by `init.sh`.

Cached results include Python pickles: only load them from a source you trust.

## License

[EUPL-1.2](LICENSE). Third-party data keep their own licences.
