#!/usr/bin/env bash
# Build the documentation site with --strict, which fails on a broken
# mkdocstrings reference or a missing cross-link.
set -euo pipefail

cd "$(dirname "$0")/.."

VENV_PY=".venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
    echo "scripts/build_docs.sh: $VENV_PY not found; create the venv first" >&2
    exit 2
fi

# The examples page links and embeds these; docs/examples/ is gitignored, so
# they must be rendered before mkdocs runs or --strict fails on a dead link.
scripts/build_examples.sh docs/examples

.venv/bin/mkdocs build --strict
echo "docs built into site/"
