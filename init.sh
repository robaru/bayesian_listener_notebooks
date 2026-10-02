#!/usr/bin/env bash
# Set up everything needed to run the notebooks and regenerate the figures.
# Safe to run repeatedly: existing environment, kernel and files are reused.
#
#   ./init.sh
#
# Environment variables:
#   BL_DATA_DIR      put the (git-ignored) data somewhere else than ./data
#   SKIP_ENV=1       do not create/update the conda environment
#   SKIP_DOWNLOAD=1  do not download HRTFs / reference data

set -u
cd "$(dirname "$0")"

ENV_NAME="bayesian_listener_notebooks"
DATA_DIR="${BL_DATA_DIR:-$PWD/data}"

if command -v wget >/dev/null 2>&1; then
    fetch() { wget -q -O "$2" "$1"; }
else
    fetch() { curl -fsSL -o "$2" "$1"; }
fi

echo "== 1/5 conda environment ($ENV_NAME)"
if [ "${SKIP_ENV:-0}" != "1" ]; then
    if ! command -v conda >/dev/null 2>&1; then
        echo "conda not found. Install Miniforge/Miniconda first: https://conda-forge.org/download/"
        exit 1
    fi
    if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
        conda env update -n "$ENV_NAME" -f environment.yml --prune
    else
        conda env create -f environment.yml
    fi
    echo "-- registering Jupyter kernel '$ENV_NAME'"
    conda run -n "$ENV_NAME" python -m ipykernel install --user \
        --name "$ENV_NAME" --display-name "Python ($ENV_NAME)"
else
    echo "skipped (SKIP_ENV=1)"
fi

echo "== 2/5 data folders under $DATA_DIR"
mkdir -p "$DATA_DIR/hrtf" "$DATA_DIR/ari" "$DATA_DIR/behavioural" \
         "$DATA_DIR/reference" "$DATA_DIR/preprocessed"
if [ "$DATA_DIR" != "$PWD/data" ] && [ ! -e "$DATA_DIR/hrtf/KEMAR_FreeFieldCompMinPhase_48kHz.sofa" ]; then
    cp data/hrtf/KEMAR_FreeFieldCompMinPhase_48kHz.sofa "$DATA_DIR/hrtf/"
fi

echo "== 3/5 downloads"
if [ "${SKIP_DOWNLOAD:-0}" != "1" ]; then
    echo "-- SONICOM participant HRTFs (33 x ~2.8 MB)"
    bash scripts/download_hrtf.sh scripts/download_hrtf.csv "$DATA_DIR/hrtf" || \
        echo "WARNING: some SONICOM downloads failed; re-run ./init.sh to retry."

    # ARI HRTFs of NH12/15/16/17/18 (Majdak et al. 2010), as distributed with
    # the Auditory Modeling Toolbox (AMT 1.0). Checksums verified against the
    # files used for the paper.
    echo "-- ARI HRTFs for Fig. 4 (5 x ~3 MB)"
    AMT_HRTF="https://sofacoustics.org/data/amt-1.0.0/hrtf/barumerli2021"
    for n in 12 15 16 17 18; do
        f="$DATA_DIR/ari/ARI_NH${n}_hrtf_M_dtf 256.sofa"
        if [ -s "$f" ]; then echo "   present: $(basename "$f")"; continue; fi
        fetch "$AMT_HRTF/ARI_NH${n}_hrtf_M_dtf%20256.sofa" "$f" \
            && echo "   ok: $(basename "$f")" \
            || { echo "   FAILED: $(basename "$f")"; rm -f "$f"; }
    done

    # Measured localisation data of Majdak et al. (2010), AMT auxdata.
    echo "-- majdak2010.mat (AMT auxdata) for Fig. 4"
    f="$DATA_DIR/reference/majdak2010.mat"
    if [ -s "$f" ]; then echo "   present: majdak2010.mat"
    else
        fetch "https://sofacoustics.org/data/amt-1.0.0/auxdata/majdak2010/data.mat" "$f" \
            && echo "   ok: majdak2010.mat" || { echo "   FAILED: majdak2010.mat"; rm -f "$f"; }
    fi
else
    echo "skipped (SKIP_DOWNLOAD=1)"
fi

echo "== 4/5 Git LFS (results/replicate_fig5_estimations.pkl)"
if command -v git-lfs >/dev/null 2>&1 || git lfs version >/dev/null 2>&1; then
    git lfs install --local >/dev/null && git lfs pull
else
    echo "WARNING: git-lfs is not installed. Fig. 4 needs the LFS file"
    echo "         results/replicate_fig5_estimations.pkl. Install git-lfs"
    echo "         (https://git-lfs.com), then run: git lfs install && git lfs pull"
fi

echo "== 5/5 behavioural data (SONICOM Ecosystem, database #58)"
BEHAV_URL="https://ecosystem.sonicom.eu/data/58/23386/41223/AXD_full_dataset_20260202.csv"
f="$DATA_DIR/behavioural/AXD_full_dataset_20260202.csv"
if [ -s "$f" ]; then echo "   present: AXD_full_dataset_20260202.csv"
else
    fetch "$BEHAV_URL" "$f" && echo "   ok: AXD_full_dataset_20260202.csv" || {
        echo "   FAILED: AXD_full_dataset_20260202.csv -- download it manually from"
        echo "   https://ecosystem.sonicom.eu/databases/58 into $DATA_DIR/behavioural/"
        echo "   (only needed to re-run notebooks 01, 05, 06, 07 and 08 from scratch)"
        rm -f "$f"; }
fi

echo
echo "Done. Next:"
echo "  conda activate $ENV_NAME"
echo "  jupyter lab                      # notebooks (kernel: $ENV_NAME)"
echo "  python -m figures.generate_all   # all paper figures -> figures/output/"
