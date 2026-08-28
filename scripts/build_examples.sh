#!/usr/bin/env bash
# Render every example under examples/ by running its spec.yaml.
#
# Each examples/<name>/spec.yaml is the canonical, literal input for that example
# -- it is what the docs show -- so rendering it here unchanged is what keeps the
# documented input and the published view the same thing. Each spec writes into
# examples/output/, relative to itself.
#
#   scripts/build_examples.sh                # -> examples/output/
#   scripts/build_examples.sh docs/examples  # -> examples/output/, then copied there
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

shopt -s nullglob
specs=(examples/*/spec.yaml)
if [[ ${#specs[@]} -eq 0 ]]; then
    echo "scripts/build_examples.sh: no examples/*/spec.yaml found" >&2
    exit 2
fi

mkdir -p examples/output
for spec in "${specs[@]}"; do
    echo "==> prot-struct-viz $spec"
    prot-struct-viz "$spec"
done

# Where a spec writes is part of the spec, so a different destination is a copy
# rather than an override. That keeps the documented command literally runnable.
DEST="${1:-examples/output}"
if [[ "$DEST" != "examples/output" ]]; then
    mkdir -p "$DEST"
    cp examples/output/* "$DEST"/
fi

echo "built ${#specs[@]} example(s) into $DEST"
