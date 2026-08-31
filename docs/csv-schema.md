# CSV schema

The CSV specifies the color, representation, and label for individual residues. A
residue with no row is drawn in the view's `default_color`, with the base representation
from `default_representation` or `chain_representation`. Heteroatoms with no row instead
keep the appearance their `waters`, `ligands`, `glycans`, and `ions` settings give them.

```csv
chain,residue,color,label,show_label,representation,label_color,label_size,notes
A,118,#67000d,Arg118,True,ball-and-stick,#67000d,2.5,Direct contact with DANA at 2.68 A
A,412A,#2171b5,,,ball-and-stick,,,Insertion-coded site
A,0,#6a51a3,DANA,True,ball-and-stick,#6a51a3,3,The bound inhibitor
```

Additional columns can be included in the CSV for your own notes, but are ignored by
this program.

## Columns

`chain` and `residue` are the chain ID and residue number as they appear in the
deposited PDB entry (author chain and residue), and as shown by the RCSB website and by
Mol\* itself. In mmCIF terms these are `auth_asym_id` and `auth_seq_id`, not the
`label_*` numbering, which runs sequentially from 1 per entity and rarely matches what a
paper cites.

| column | required | meaning |
| --- | --- | --- |
| `chain` | yes | PDB (author) chain ID, e.g. `A`. |
| `residue` | yes | PDB (author) residue number, read as a string so insertion codes work. |
| `color` | yes | Hex (`#1f77b4`, `#abc`) or a CSS color name (`red`), normalized to `#rrggbb`. |
| `label` | no | Text shown on **mouseover**. |
| `show_label` | no | `True` also draws `label` permanently on the structure. |
| `representation` | no | An **additional** representation for this residue, drawn on top of the base one. |
| `label_color` | no | Color of the on-structure label text. Default black. |
| `label_size` | no | Height of the on-structure label text, in Angstroms. Default 2. |

`residue` being a string is what makes `412`, `412A`, and `412B` three different
residues. It also means `0169` is not `169`; write the number as the structure does.

`label` and `show_label` are separate on purpose: a residue can have a tooltip only, a
tooltip that is also drawn on the structure, or neither. `show_label = True` with an
empty `label` is an error — there would be nothing to draw. Keep `label` short, and put
lengthy notes in a column of your own (`notes`, say).

Possible values for `representation` are described under
[the spec reference](spec.md#representation-layers-and-heteroatoms).

## Styling on-structure text labels

`label_color` and `label_size` control how a persistent label is drawn. Size is a text
height in **Angstroms of world space**, not screen pixels, so a label keeps its size
relative to the structure as you zoom. Mol\*'s own default of 1 A is about a bond length
and reads very small beside a residue, so the default here is 2.

## Parsing is strict

These are all fatal, and name the CSV line and column:

- a missing required column, or a blank required cell;
- an invalid color, or a `residue` that is not a number with an optional insertion code;
- a `show_label` that is not `True`, `False`, or empty;
- an unknown `representation`;
- a duplicated `(chain, residue)`, or a duplicated column name.

No value is ever substituted for a missing one — the only default that applies to *cells*
is `show_label`, which is `False` when absent.
