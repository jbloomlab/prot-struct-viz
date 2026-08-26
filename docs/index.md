# prot-struct-viz

Render a protein structure as a **self-contained static HTML file** using
[Mol*](https://molstar.org/), with residues colored, labeled, and styled from a CSV.

The whole view — coordinates, colors, tooltips, labels, and the Mol* state that ties
them together — is embedded in the one HTML file, so it can be hosted on GitHub Pages
with no backend. Mol* itself is loaded from a CDN, so viewing needs an internet
connection.

## Install

```bash
pip install -e .
```

## Quick start

```bash
prot-struct-viz \
  --structure 1F8B \
  --csv examples/coloring.csv \
  --assembly 1 \
  --out view.html
```

This writes `view.html` and `view_report.txt`. See the
[CSV schema](csv-schema.md) for what goes in the CSV, and the
[CLI reference](cli.md) for the full set of options.

## How it works

1. The structure is fetched from RCSB (or read from a local file) and its deposited
   residues are enumerated in author numbering, each classified as polymer, glycan,
   ligand, ion, or water.
2. The CSV is parsed strictly, and its residue set is checked against the structure's
   addressable residues. The result goes into the report file.
3. A [MolViewSpec](https://molstar.org/mol-view-spec-docs/) state plus a JSON annotation
   table are zipped with the coordinates into an MVSX archive, embedded base64 in the
   HTML, and loaded by Mol* in the browser.

Because the annotations are MVS tables rather than baked-in colors, the Mol* UI stays
fully usable: everything the file sets is the *initial* state, and representations and
colorings can be changed live in the Components panel.

## Assemblies

Only the deposited asymmetric unit is embedded, alongside an assembly id. Mol* generates
the symmetry copies in the browser, so a high-symmetry entry does not blow up the file
size. A CSV row applies to every symmetry copy of the chain it names, and validation
always runs against the deposited chains, so it does not change with `--assembly`.
