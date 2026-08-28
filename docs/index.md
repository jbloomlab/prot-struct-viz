# prot-struct-viz

Render a protein structure as a **self-contained static HTML file** using
[Mol\*](https://molstar.org/), with residues colored, labeled, and styled from a CSV.

Everything the view needs — coordinates, colors, tooltips, labels — is embedded in the
one file, so it can be dropped on any static host with no backend. See the
[examples](examples.md) for a live one.

## Install

```bash
pip install prot-struct-viz
```

Or from a checkout, which is also how you get the development and docs extras:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
```

## Quick start

Write a CSV naming the residues you want to say something about:

```csv
chain,residue,color,label,show_label
A,118,#67000d,Arg118,True
A,119,#cb181d,Glu119,
```

Then write a spec file saying what to draw and where to put it:

```yaml
# spec.yaml
structure: 1F8B
out: view.html
assembly: "1"
on_mismatch: report

views:
  - name: Active site
    csv: coloring.csv
    default_color: "#d9d9d9"
    default_representation: cartoon
    waters: hide
    ligands: show
    glycans: snfg
    ions: show
```

```bash
prot-struct-viz spec.yaml
```

That writes `view.html` (the page) and `view_report.txt` (the progress log, and a report
on any disagreement between the CSV and the structure).

The spec is the whole input: there are no other flags. Every key is listed in the
[spec reference](spec.md).

## Several views of one structure

A spec may list more than one view, and the page then offers a selector. Views are
independent — each has its own CSV, colors, labels, representation, and heteroatom
settings — but they share one structure and one camera, so switching between them
does not move the view:

```yaml
views:
  - name: Antigenic sites
    csv: antigenic.csv
    default_representation: surface
    # ... the rest of the required keys
  - name: Receptor contacts
    csv: contacts.csv
    default_representation: cartoon
    glycans: hide
    # ... the rest of the required keys
```

The format fills in no defaults: every view states its own options. Use a YAML anchor
to say the shared part once.

## Sharing the view

The output is a single file with no server side, so committing it to a repository with
GitHub Pages enabled is all that is needed:

```bash
mkdir -p docs && cp view.html docs/
git add docs/view.html && git commit -m "Add structure view" && git push
```

Set Pages to serve from `/docs` on the default branch, and the view is at
`https://<org>.github.io/<repo>/view.html`.

## Where to go next

- **[Examples](examples.md)** — rendered views, with the command and inputs that made them.
- **[Spec reference](spec.md)** — every key, plus assemblies, representation layers,
  heteroatoms, and checking the CSV against the structure.
- **[CSV schema](csv-schema.md)** — every column, and what makes a CSV invalid.
- **[The rendered page](viewer.md)** — what a reader of the output can click.
- **[Python API](python-api.md)** — building a spec in Python instead of YAML.
- **[How it works](internals.md)** — the MolViewSpec pipeline, for anyone extending this.
