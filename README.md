# prot-struct-viz

Render a protein structure as a **self-contained static HTML file** using
[Mol*](https://molstar.org/), with residues colored, labeled, and styled from a CSV.
Everything the view needs — coordinates, colors, tooltips, labels — is embedded in the
one file, so it can be dropped on GitHub Pages with no backend.

Full documentation: <https://jbloomlab.github.io/prot-struct-viz/>

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Worked example

Influenza B neuraminidase with the residues that contact the DANA inhibitor shaded by
distance, insertion-coded sites marked, and one glycan recolored from the CSV:

```bash
prot-struct-viz \
  --structure 1F8B \
  --csv examples/coloring.csv \
  --title-md examples/title.md \
  --assembly 1 \
  --out examples/output/1f8b_active_site.html
```

That writes `1f8b_active_site.html` (the view) and `1f8b_active_site_report.txt` (the
progress log and mismatch report). `python examples/build_example.py` does the same
through the Python API.

## The CSV

One row per residue you want to say something about. Required columns are `chain`,
`residue`, and `color`; `label`, `show_label`, and `representation` are optional.

```csv
chain,residue,color,label,show_label,representation,label_color,label_size,notes
A,118,#67000d,Arg118,True,ball-and-stick,#67000d,2.5,Contacts the ligand at 2.68 A
A,412A,#2171b5,,,ball-and-stick,,,Insertion-coded site
```

- `chain` is the deposited **author** chain ID, and `residue` the **author** residue
  number. `residue` is read as a string, so insertion codes (`412A`) work and are
  distinct from the plain number (`412`).
- `label` is the mouseover tooltip. `show_label` additionally draws that text on the
  structure, so a residue can have a tooltip, a permanent label, both, or neither.
- `representation` is **additive**: it draws on top of the base representation, which is
  how you get the usual cartoon backbone with sticks on key residues.
- `label_color` and `label_size` style the on-structure label. Size is a text height in
  Angstroms of world space, so labels scale with the structure; it defaults to 2, and the
  color to black.
- Several colorings can live in one file as `color:<SchemeName>` columns instead of a
  bare `color`. All are parsed and reported; the first is the one rendered.
- **Any other columns are ignored**, so the file can carry your own notes, an
  alternative numbering, or whatever else belongs beside the residue. Keep labels short
  — they are drawn in the 3D scene — and put the explanation in a column of your own.

Parsing is strict. A missing column, a blank required cell, an invalid color, an
unparseable residue number, or a duplicated `(chain, residue)` is a fatal error naming
the line and column, and every offending line is reported at once. Nothing is guessed.

Residues with **no CSV row at all** are a different matter: they render in
`--default-color`.

## Checking the CSV against the structure

`--on-mismatch` decides what happens when the CSV and the structure disagree about
which residues exist. A report file is written in **every** mode, including the fatal
ones, so a failed run still leaves a record.

| mode | fatal when |
| --- | --- |
| `error-any` | the CSV or the structure has residues the other lacks |
| `error-extra-in-pdb` | the structure has residues the CSV omits |
| `error-extra-in-csv` | the CSV has rows with no matching residue |
| `report` | never; mismatches are reported and the run continues |

Validation always runs against the deposited asymmetric unit, so it does not change
with `--assembly`. Waters are excluded from the addressable set — they would otherwise
swamp the report — so a CSV row landing on one gets a message pointing at `--waters`.

## Representations and heteroatoms

The representation of a residue is built in three layers: the global
`--default-representation`, overridden per chain by `--chain-representation`, with the
CSV's `representation` column added on top per residue.

`--waters`, `--ligands`, `--glycans`, and `--ions` set the **baseline** for heteroatoms
the CSV does not name: ligands and ions element-colored, glycans as 3D-SNFG symbols.
**A residue named in the CSV always wins.** Naming a glycan gives it the CSV color and
representation instead of its SNFG symbol (a recolored SNFG symbol would be
meaningless); naming a ligand replaces element coloring with a flat CSV color. Sugars
and ligands the CSV does not mention keep their standard appearance, so the two color
languages never fight over the same atoms.

Because a cartoon draws nothing for a ligand or an ion, a CSV-named non-polymer residue
gets ball-and-stick as its base rather than the polymer base representation.

## Assemblies

`--assembly au` shows the deposited asymmetric unit; `--assembly 1` (or any id the entry
defines) shows a biological assembly. Only the deposited coordinates are embedded, plus
the assembly id — Mol\* generates the symmetry copies in the browser, so the file stays
small even for high-symmetry entries. A CSV row applies to every symmetry copy of the
chain it names.

## Hosting on GitHub Pages

The output is a single file with no server side, so committing it to a repository with
Pages enabled is all that is needed:

```bash
mkdir -p docs && cp view.html docs/
git add docs/view.html && git commit -m "Add structure view" && git push
```

Then set Pages to serve from `/docs` on the default branch; the view is at
`https://<org>.github.io/<repo>/view.html`. Note that while all the *data* is inline,
Mol\* itself is loaded from a CDN, so viewing needs an internet connection.

## Development

```bash
pip install -e ".[dev,docs]"
scripts/check.sh          # pytest + ruff + black
scripts/build_docs.sh     # mkdocs build --strict
```

Conventions, and the checks to run after changing anything that affects rendering, are
in [`CLAUDE.md`](CLAUDE.md).
