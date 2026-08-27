#!/usr/bin/env bash
# Influenza B neuraminidase (PDB 1F8B), biological tetramer, with the active-site
# residues that contact the DANA inhibitor shaded by distance.
#
# Writes into $OUT_DIR (default: this directory's output/). Run it directly, or
# run every example at once with scripts/build_examples.sh.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p "${OUT_DIR:=output}"

prot-struct-viz \
  --structure 1F8B \
  --csv coloring.csv \
  --chain-representation chains.csv \
  --title-md title.md \
  --assembly 1 \
  --waters hide \
  --out "$OUT_DIR/1f8b_active_site.html"
