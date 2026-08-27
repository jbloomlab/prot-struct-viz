#!/usr/bin/env bash
# Render every example under examples/ by running its command.sh.
#
# Each examples/<name>/command.sh is the canonical, literal CLI invocation for
# that example -- it is what the docs show -- so running it here is what keeps
# the documented command and the published view the same thing.
#
#   scripts/build_examples.sh                # -> examples/output/
#   scripts/build_examples.sh docs/examples  # -> docs/examples/ (for mkdocs)
set -euo pipefail

cd "$(dirname "$0")/.."
REPO_ROOT="$PWD"

# The examples invoke `prot-struct-viz` by name. Locally that lives in .venv;
# in CI the package is installed into the runner's own Python and is already on
# $PATH. Prefer the venv when there is one, rather than requiring it -- this
# script runs in both places.
if [[ -x "$REPO_ROOT/.venv/bin/prot-struct-viz" ]]; then
    export PATH="$REPO_ROOT/.venv/bin:$PATH"
fi
if ! command -v prot-struct-viz >/dev/null; then
    echo "scripts/build_examples.sh: prot-struct-viz not on \$PATH;" \
         "create the venv or 'pip install -e .' first" >&2
    exit 2
fi

OUT_DIR_ARG="${1:-examples/output}"
mkdir -p "$OUT_DIR_ARG"
# command.sh cd's into its own directory, so it needs an absolute OUT_DIR.
OUT_DIR="$(cd "$OUT_DIR_ARG" && pwd)"
export OUT_DIR

shopt -s nullglob
commands=(examples/*/command.sh)
if [[ ${#commands[@]} -eq 0 ]]; then
    echo "scripts/build_examples.sh: no examples/*/command.sh found" >&2
    exit 2
fi

for cmd in "${commands[@]}"; do
    echo "==> $cmd"
    bash "$cmd"
done

echo "built ${#commands[@]} example(s) into $OUT_DIR_ARG"
