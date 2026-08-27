#!/usr/bin/env bash
# Influenza A/Victoria/2570/2019 (H1N1)pdm09 hemagglutinin, uncleaved (PDB
# 9GSP), with HA1 colored by classical antigenic site and every residue labeled
# with its site number.
#
# The protein is a surface, which is how an antigenic site reads as a patch an
# antibody could land on rather than a scatter of colored ribbon. Every sugar is
# named in coloring.csv, so --glycans never applies: the N-glycans are yellow
# ball-and-stick rather than SNFG symbols.
#
# Two flags the H3 example next door needs and this one does not. There is no
# --assembly: 9GSP deposits the whole trimer, so the annotation covers three
# chains and there is no symmetry for Mol* to expand. There is no --waters hide
# either -- this is a cryo-EM entry with no modeled waters to hide.
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
  --structure 9GSP \
  --csv coloring.csv \
  --title-md title.md \
  --default-representation surface \
  --on-mismatch error-extra-in-csv \
  --out "$OUT_DIR/9gsp_antigenic_regions.html"
