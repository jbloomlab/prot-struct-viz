# prot-struct-viz

[![PyPI version](https://img.shields.io/pypi/v/prot-struct-viz.svg)](https://pypi.org/project/prot-struct-viz/)
[![Python versions](https://img.shields.io/pypi/pyversions/prot-struct-viz.svg)](https://pypi.org/project/prot-struct-viz/)
[![tests](https://github.com/jbloomlab/prot-struct-viz/actions/workflows/tests.yml/badge.svg)](https://github.com/jbloomlab/prot-struct-viz/actions/workflows/tests.yml)
[![Docs](https://img.shields.io/github/deployments/jbloomlab/prot-struct-viz/github-pages?label=docs)](https://jbloomlab.github.io/prot-struct-viz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

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

Write a CSV of the residues you want to say something about, and a spec file naming the
structure, where the HTML goes, and one or more **views** of it. Then:

```bash
prot-struct-viz spec.yaml
```

That writes the page, plus a report on any disagreement between the CSV and the
structure. One spec can hold several named views — different colorings, labels,
representations, or heteroatoms — and the page gets a selector that switches between them
without moving the camera. The URL tracks the selector, so a link can point at one
particular view.

The [quick start](https://jbloomlab.github.io/prot-struct-viz/#quick-start) shows both
files in full; the documentation covers every spec key, the CSV columns, and what a
reader of the output can click.

## Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,docs]"

scripts/check.sh            # pytest + ruff + black
scripts/build_examples.sh   # render examples/*/spec.yaml into examples/output/
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
