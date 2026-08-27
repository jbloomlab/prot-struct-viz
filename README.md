# prot-struct-viz

[![tests](https://github.com/jbloomlab/prot-struct-viz/actions/workflows/tests.yml/badge.svg)](https://github.com/jbloomlab/prot-struct-viz/actions/workflows/tests.yml)
[![docs](https://github.com/jbloomlab/prot-struct-viz/actions/workflows/docs.yml/badge.svg)](https://jbloomlab.github.io/prot-struct-viz/)

Render a protein structure as a **self-contained static HTML file** using
[Mol\*](https://molstar.org/), with residues colored, labeled, and styled from a CSV.
Everything the view needs — coordinates, colors, tooltips, labels — is embedded in the one
file, so it can be dropped on GitHub Pages with no backend.

- **Documentation:** <https://jbloomlab.github.io/prot-struct-viz/>
- **Live example:** <https://jbloomlab.github.io/prot-struct-viz/examples/>

## Install

```bash
pip install prot-struct-viz
```

## Quick start

```bash
prot-struct-viz \
  --structure 1F8B \
  --csv coloring.csv \
  --assembly 1 \
  --out view.html
```

That writes `view.html` and `view_report.txt`. The
[CSV schema](https://jbloomlab.github.io/prot-struct-viz/csv-schema/) covers what goes in
the CSV, and the
[rendering options](https://jbloomlab.github.io/prot-struct-viz/rendering/) cover
assemblies, representations, and heteroatoms.

## Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,docs]"

scripts/check.sh            # pytest + ruff + black
scripts/build_examples.sh   # render examples/*/command.sh into examples/output/
scripts/build_docs.sh       # mkdocs build --strict
```

Documentation lives in `docs/`, which is the single source — this README is a front door,
not a second copy. Conventions, and the checks to run after changing anything that affects
rendering, are in [`CLAUDE.md`](CLAUDE.md).

### Releasing

Releases are tag-driven and publish to PyPI through
[trusted publishing](https://docs.pypi.org/trusted-publishers/), so no API token is
stored in the repo. The one-time PyPI setup and the per-release recipe are documented at
the top of [`.github/workflows/release.yml`](.github/workflows/release.yml). In short:

```bash
# 1. Bump `version` in pyproject.toml and roll CHANGELOG's [Unreleased] into it.
git commit -am "release vX.Y.Z"
git tag vX.Y.Z
git push && git push --tags
```

The workflow verifies the tag matches `pyproject.toml` before anything reaches PyPI.
