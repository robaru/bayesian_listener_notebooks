# Notebooks

| Notebook | Paper | Content |
|---|---|---|
| `00_replicate_barumerli2023_fig5` | Sec. 3.1, Fig. 4 | Python vs MATLAB implementation |
| `01_interpolation_comparison` | Sec. 3.2 | template error per interpolation method |
| `02_generate_parameter_sets` | Sec. 2.3 | 28 ground-truth parameter sets |
| `03_nll_stability` | Sec. 3.3, Fig. S2 | number of Monte Carlo samples |
| `04_parameter_recovery` | Sec. 3.3, Fig. S3 | parameter recovery on simulated data |
| `05_estimate_motor_noise` | Sec. 2.2.2 | motor noise from lateral errors |
| `06_sensitivity_sigma_itd_ild` | Sec. 3.4 | sensitivity to fixed σ_itd / σ_ild |
| `07_fit_all_participants` | Sec. 3.4, Table 1 | fits to 33 participants |
| `08_posterior_predictive_checks` | Sec. 3.4.1, 3.5, Tables 1–2 | posterior predictive checks, BIC |
| `09_verify_reported_statistics` | all | checks the reported statistics |

Open them with `jupyter lab` and the kernel `bayesian_listener_notebooks` (set up by `../init.sh`).
All file locations are defined in `paths.py`.

Notebooks with cached results in `../results/` load them instead of recomputing. Re-running
`03`, `04`, `07` and `08` from scratch takes hours; `07` only refits when `RUN_FITTING = True`.
Order of dependencies: `02` → `03`, `04`; `07` → `08` → `09`, `../stats/` and the figures.
