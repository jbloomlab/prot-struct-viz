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

`chain` and `residue` are **author** numbering: the chain ID and residue number as they
appear in the deposited PDB entry, and as shown by the RCSB website and by Mol\* itself.
In mmCIF terms these are `auth_asym_id` and `auth_seq_id`, not the `label_*` numbering,
which runs sequentially from 1 per entity and rarely matches what a paper cites. If you
read a residue number off a figure or a structure viewer, it is the author number.

| column | required | meaning |
| --- | --- | --- |
| `chain` | yes | PDB (author) chain ID, e.g. `A`. |
| `residue` | yes | PDB (author) residue number, read as a string so insertion codes work. |
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

Any column not listed above is ignored by the renderer. A `notes` column is the usual
use: it records what each site is, while `label` stays short enough to draw. Nothing
stops you adding an alternative numbering, a source citation, or a p-value alongside.

`representation` is described under
[rendering options](rendering.md#representations-and-heteroatoms), since it is one layer
of a model that the command-line flags also feed into.

## Styling the on-structure label

`label_color` and `label_size` control how a persistent label is drawn. Size is a text
height in **Angstroms of world space**, not screen pixels, so a label keeps its size
relative to the structure as you zoom. Mol\*'s own default of 1 A is about a bond length
and reads very small beside a residue, so the default here is 2.

Both columns style the persistent label only, so they do nothing on a row whose
`show_label` is not `True`. That is deliberately not an error: it lets you set a color on
every row and toggle `show_label` freely while working on a figure.

## Several colorings of one structure

Several colorings are several CSVs, one per view in the [spec file](cli.md) — not several
columns in one CSV. A view is a whole presentation, so its CSV can differ in labels,
tooltips and per-residue representations too, not only in color.

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
