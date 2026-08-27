#!/usr/bin/env bash
# Influenza A/Victoria/22/2020 (H3N2) hemagglutinin with the LSTc receptor
# analogue bound (PDB 8FAW), as the biological trimer, with HA1 colored by
# classical antigenic region and every residue labeled with its site number.
#
# --on-mismatch error-extra-in-csv is the one departure from the defaults:
# coloring.csv is machine-generated from a numbering map, so a numbering slip
# would otherwise be a quiet line in the report rather than a failed build.
#
# Writes into $OUT_DIR (default: this directory's output/). Run it directly, or
# run every example at once with scripts/build_examples.sh.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p "${OUT_DIR:=output}"

prot-struct-viz \
  --structure 8FAW \
  --csv coloring.csv \
  --title-md title.md \
  --assembly 1 \
  --waters hide \
  --on-mismatch error-extra-in-csv \
  --out "$OUT_DIR/8faw_antigenic_regions.html"
