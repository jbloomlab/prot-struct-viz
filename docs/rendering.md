# Rendering options

Everything on this page is set from the command line (or the equivalent `ViewConfig`
field). The [CLI reference](cli.md) lists every flag and its exact spelling; this page
explains what they mean together.

## Assemblies

`--assembly` chooses what the browser shows:

| value | shows |
| --- | --- |
| `au` (default) | the deposited asymmetric unit, exactly as in the file |
| `1`, `2`, … | a biological assembly, using any id the entry defines |

A CSV row applies to **every symmetry copy** of the chain it names, so a residue
highlighted in one subunit is highlighted in all of them, and a persistent label is drawn
once per copy.

Validation always runs against the deposited chains, so it does not change with
`--assembly`. A row naming a residue that exists in the entry but is not part of the
chosen assembly is reported separately rather than treated as a mismatch.

## Representations and heteroatoms

The representation of a residue is built in three layers:

1. `--default-representation` sets the global base.
2. `--chain-representation` overrides that base for whole chains.
3. The CSV's `representation` column is **added on top**, per residue.

The third layer being additive is what produces the standard figure: a cartoon backbone
with sticks on a handful of key residues. Allowed values at every layer are `cartoon`,
`ball-and-stick`, `spacefill`, `surface`, and `carbohydrate`.

`--chain-representation` takes a small CSV:

```csv
chain,representation
A,cartoon
B,surface
```

This sets the base for each chain's **polymer** only. A CSV-named ligand or ion on that
chain still gets ball-and-stick, because a cartoon or a surface draws nothing for a
single heteroatom residue.

`--waters`, `--ligands`, `--glycans`, and `--ions` set the **baseline** appearance for
heteroatoms the CSV does not name: ligands and ions element-colored, glycans as 3D-SNFG
symbols.

**A residue named in the CSV always wins.** Naming a glycan gives it the CSV color and
representation instead of its SNFG symbol — a recolored SNFG symbol would be meaningless
— and naming a ligand replaces element coloring with the flat CSV color. Sugars and
ligands the CSV does not mention keep their standard appearance, so the two color
languages never fight over the same atoms.

## Checking the CSV against the structure

`--on-mismatch` decides what happens when the CSV and the structure disagree about which
residues exist. A report file is written in **every** mode, including the fatal ones, so
a failed run still leaves a record of what went wrong.

| mode | fatal when |
| --- | --- |
| `error-any` | the CSV or the structure has residues the other lacks |
| `error-extra-in-pdb` | the structure has residues the CSV omits |
| `error-extra-in-csv` | the CSV has rows with no matching residue |
| `report` | never; mismatches are reported and the run continues |

Waters are excluded from the addressable set — they would otherwise swamp the report — so
a CSV row landing on a water gets a message pointing at `--waters` rather than a generic
"no such residue".

## Choosing what to draw

`--chains` narrows the view to the chains you name. It is a display filter only:
validation still runs against every deposited chain, and rows for excluded chains are
reported as a separate warning rather than as mismatches.

`--default-color` sets the color of every residue with no CSV row.

`--title-md` renders a Markdown file into a header block above the viewer, which is where
a caption, a legend, or a link back to the source belongs.

## Getting the structure

`--structure` takes either a PDB ID to fetch from RCSB, or a path to a local
`.cif`/`.pdb` file (`.gz` is decompressed transparently).

Downloads are **not** cached. Only the coordinate text is used, and it ends up embedded
in the output, so a cache would save one HTTP request at the price of a stale-file
failure mode. If you are re-rendering the same entry repeatedly, download it once and
pass the path.
