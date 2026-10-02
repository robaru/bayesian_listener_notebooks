"""Single source of truth for every file location used by the notebooks,
the figure scripts and (by convention) the R analysis.

Notebooks (in ``notebooks/``) simply ``import paths``. Figure scripts run as
``python -m figures.generate_all`` from the repository root and use
``from notebooks.paths import ...``.

Input data (HRTFs, behavioural data, preprocessed caches) live under
``data/``, which is git-ignored except for the KEMAR SOFA file and the list of target
directions. Set the
environment variable ``BL_DATA_DIR`` to keep the data somewhere else::

    export BL_DATA_DIR=/path/to/my/data

Cached analysis results (read by the figure scripts and by ``stats/``) live in
``results/``; generated figures go to ``figures/output/``.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # repository root

DATA_DIR = Path(os.environ.get("BL_DATA_DIR", ROOT / "data")).expanduser().resolve()
HRTF_DIR = DATA_DIR / "hrtf"                 # SONICOM SOFA files (P*.sofa + KEMAR)
ARI_DIR = DATA_DIR / "ari"                   # ARI NH12/15/16/17/18 SOFA files (Fig. 4)
BEHAV_DIR = DATA_DIR / "behavioural"         # AXD_full_dataset_20260202.csv (downloaded by init.sh)
REFERENCE_DIR = DATA_DIR / "reference"       # majdak2010.mat (AMT auxdata, Fig. 4)
CACHE_DIR = DATA_DIR / "preprocessed"        # bayesian_listener feature cache

RESULTS_DIR = ROOT / "results"
FIG_DIR = ROOT / "figures" / "output"

# Frequently used files
KEMAR_SOFA = HRTF_DIR / "KEMAR_FreeFieldCompMinPhase_48kHz.sofa"
BEHAV_FILE = BEHAV_DIR / "AXD_full_dataset_20260202.csv"
DIRS_FILE = ROOT / "data" / "target_directions.csv"   # 33 target directions (tracked)
FITTING_RESULTS = RESULTS_DIR / "fitting_results.csv"


def participant_sofa(participant_id):
    """Path of a participant's SONICOM HRTF (as downloaded by download_hrtf.sh)."""
    return HRTF_DIR / f"{participant_id}_FreeFieldCompMinPhase_48kHz.sofa"


def ari_sofa(subject_id):
    """Path of an ARI HRTF, e.g. ``ari_sofa('nh12')``."""
    return ARI_DIR / f"ARI_{subject_id.upper()}_hrtf_M_dtf 256.sofa"
