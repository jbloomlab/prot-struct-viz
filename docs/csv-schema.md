# CSV schema

One row per residue you want to say something about. Residues with no row at all render
in `--default-color`.

```csv
chain,residue,color,label,show_label,representation,label_color,label_size,notes
A,118,#67000d,Arg118,True,ball-and-stick,#67000d,2.5,Direct contact with DANA at 2.68 A
A,412A,#2171b5,,,ball-and-stick,,,Insertion-coded site
A,0,#6a51a3,DANA,True,ball-and-stick,#6a51a3,3,The bound inhibitor
```

Columns beyond the ones below are ignored, so the CSV can carry whatever else belongs
beside a residue.

## Columns

| column | required | meaning |
| --- | --- | --- |
| `chain` | yes | Deposited **author** chain ID, e.g. `A`. |
| `residue` | yes | **Author** residue number, read as a string so insertion codes work. |
| `color` | yes | Hex (`#1f77b4`, `#abc`) or a CSS color name (`red`), normalized to `#rrggbb`. |
| `label` | no | Text shown on **mouseover**. |
| `show_label` | no | `True` also draws `label` permanently on the structure. |
| `representation` | no | An **additional** representation for this residue. |
| `label_color` | no | Color of the on-structure label text. Default black. |
| `label_size` | no | Height of the on-structure label text, in Angstroms. Default 2. |

`residue` being a string is what makes `412`, `412A`, and `412B` three different
residues. It also means `0169` is not `169`; write the number as the structure does.

`label` and `show_label` are separate on purpose: a residue can have a tooltip only, a
tooltip that is also drawn on the structure, or neither. `show_label = True` with an
empty `label` is an error — there would be nothing to draw.

Keep `label` short. It is drawn into the 3D scene, where a sentence is unreadable and
crowds out the structure. Put the explanation in a column of your own instead:

## Your own columns

Any column that is not one of the six above is ignored by the renderer. `examples/coloring.csv`
uses a `notes` column this way, recording what each site is while the `label` column stays
down to `Arg118`. Nothing stops you adding an alternative numbering, a source citation, or
a p-value alongside.

`representation` is additive, drawn on top of the base representation. That is how you
get the standard figure of a cartoon backbone with sticks on a handful of key residues.
Allowed values are `cartoon`, `ball-and-stick`, `spacefill`, `surface`, and
`carbohydrate`.

## Styling the on-structure label

`label_color` and `label_size` control how a persistent label is drawn. Size is a text
height in **Angstroms of world space**, not screen pixels, so a label keeps its size
relative to the structure as you zoom. Mol*'s own default of 1 A is about a bond length
and reads very small beside a residue, so the default here is 2.

Both columns style the persistent label only, so they do nothing on a row whose
`show_label` is not `True`. That is deliberately not an error: it lets you set a color on
every row and toggle `show_label` freely while working on a figure.

## Several colorings in one file

Replace the bare `color` column with one or more `color:<SchemeName>` columns:

```csv
chain,residue,color:Entropy,color:Escape
A,118,#67000d,#2171b5
```

All schemes are parsed and named in the report. The first is the one rendered; a
selector for switching between them in the browser is not implemented yet. Mixing a bare
`color` column with `color:<Scheme>` columns is an error.

## Parsing is strict

These are all fatal, and name the CSV line and column:

- a missing required column, or a blank required cell;
- an invalid color, or a `residue` that is not a number with an optional insertion code;
- a `show_label` that is not `True`, `False`, or empty;
- an unknown `representation`;
- a duplicated `(chain, residue)`, or a duplicated column name.

Every offending line is reported at once, so one run tells you everything to fix. No
value is ever substituted for a missing one — the only default that applies to *cells*
is `show_label`, which is `False` when absent.

## Per-chain representations

`--chain-representation` takes a small CSV that overrides the base representation for
whole chains:

```csv
chain,representation
A,cartoon
B,surface
```

This sets the base for each chain's **polymer**. A CSV-named ligand or ion on that chain
still gets ball-and-stick, because a cartoon or surface draws nothing for a single
heteroatom residue.
