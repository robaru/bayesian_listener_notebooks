#!/usr/bin/env bash
# Download participant HRTFs (FreeFieldCompMinPhase, 48 kHz) from the SONICOM
# HRTF dataset (Engel et al. 2023, CC BY 4.0).
#
# Usage: ./download_hrtf.sh <csv_file> [output_directory]
#   <csv_file>          one SONICOM id per line (e.g. P0001), first line is a header
#   [output_directory]  default: ./data/hrtf
#
# Files that already exist (and are non-empty) are skipped. Uses wget if
# available, otherwise curl.

set -u

if [ $# -lt 1 ]; then
    echo "Usage: $0 <csv_file> [output_directory]"
    echo "Example: $0 download_hrtf.csv data/hrtf"
    exit 1
fi

CSV_FILE="$1"
OUTPUT_DIR="${2:-./data/hrtf}"

if [ ! -f "$CSV_FILE" ]; then
    echo "Error: CSV file '$CSV_FILE' not found!"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

BASE_URL="https://transfer.ic.ac.uk:9090/2022_SONICOM-HRTF-DATASET"

if command -v wget >/dev/null 2>&1; then
    fetch() { wget --no-check-certificate -q -O "$2" "$1"; }
elif command -v curl >/dev/null 2>&1; then
    fetch() { curl -fsSL --insecure -o "$2" "$1"; }
else
    echo "Error: neither wget nor curl is installed."
    exit 1
fi

total=0
success=0
skipped=0
failed=0

echo "Starting HRTF downloads..."
echo "Output directory: $OUTPUT_DIR"
echo "================================"

# Read CSV file, skip header (process substitution keeps the counters in this shell)
while IFS=, read -r hrtf_id || [ -n "$hrtf_id" ]; do
    hrtf_id=$(echo "$hrtf_id" | tr -d '[:space:]')
    [ -z "$hrtf_id" ] && continue

    total=$((total + 1))
    name=$(basename "$hrtf_id")
    url="${BASE_URL}/${hrtf_id}/HRTF/HRTF/48kHz/${name}_FreeFieldCompMinPhase_48kHz.sofa"
    output_file="${OUTPUT_DIR}/${name}_FreeFieldCompMinPhase_48kHz.sofa"

    if [ -s "$output_file" ]; then
        skipped=$((skipped + 1))
        echo "[$total] Present, skipping: $name"
        continue
    fi

    echo "[$total] Downloading: $name"
    if fetch "$url" "$output_file"; then
        success=$((success + 1))
        echo "  ok: $output_file"
    else
        failed=$((failed + 1))
        echo "  FAILED: $name ($url)"
        rm -f "$output_file"
    fi
done < <(tail -n +2 "$CSV_FILE")

echo "================================"
echo "Total: $total  downloaded: $success  already present: $skipped  failed: $failed"
[ "$failed" -eq 0 ]
