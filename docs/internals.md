# How it works

Nothing on this page is needed to use `prot-struct-viz`. It is here for anyone extending
the package, or wondering why the output file is shaped the way it is.

## The pipeline

1. The structure is fetched from RCSB (or read from a local file) and its deposited
   residues are enumerated in author numbering, each classified as polymer, glycan,
   ligand, ion, or water.
2. The CSV is parsed strictly, and its residue set is checked against the structure's
   addressable residues. The result goes into the report file.
3. A [MolViewSpec](https://molstar.org/mol-view-spec-docs/) state plus a JSON annotation
   table are zipped with the coordinates into an MVSX archive, embedded base64 in the
   HTML, and loaded by Mol\* in the browser.

## Annotation tables, not baked-in colors

An **annotation table** is a MolViewSpec concept: a table of rows, each selecting some
residues and carrying a value — a color, a tooltip. The Mol\* state references the table
rather than naming every atom, and Mol\* resolves the rows at load time.

The consequence is worth knowing even as a user: everything the file sets is the
*initial* state, not a frozen picture. The Components panel stays usable, so a reader of
your figure can restyle what is there or turn a component off.

There is one real limit, and it follows from where the colors hang. `color_from_uri` is a
child of each **representation** node, so Mol\* resolves the annotation rows into the
representations the file created and nowhere else. A representation you add yourself from
the Components panel is a new node with no annotation attached: it arrives in Mol\*'s own
element coloring and cannot be recolored from the CSV through the UI. This is a property
of MolViewSpec rather than a setting — the format has no structure-level or global color
node, only per-representation ones.

Tooltips and labels are unaffected, because they attach higher up: `tooltip_from_uri` is
on the structure node, and the persistent labels are primitives on the structure. So a
representation you add still shows the CSV tooltips on mouseover; only the color is
missing.

The **Reset view** button reloads the state from the archive still embedded in the page,
which restores the coloring and the starting camera.

Being primitives rather than components is also why the page carries its own **Labels**
checkbox: the labels are not an entry in the Components panel that a reader would find and
switch off. The checkbox hides the representation Mol\* builds for each primitives group, so
one click covers every label and every symmetry copy of it.

## What the components are called

Mol\* names each entry in the Components panel after the annotation field and value it
selects on, which is why they read as `MVS Annotation Component (base_rep: surface)`
rather than something friendlier. The fields are ours:

- `base_rep` — the base representation for a group of residues: from
  `--default-representation` or `--chain-representation`, or ball-and-stick for a
  heteroatom the CSV names.
- `extra_rep` — the additive layer from the CSV's `representation` column.
- `het_layer` — a default heteroatom group (`ligand`, `glycan`, `ion`, `water`) holding
  residues the CSV does not name.

Mol\* composes that label itself, and MolViewSpec has no field for overriding it.

## Why only the asymmetric unit is embedded

`--assembly` does not expand symmetry copies into the file. The deposited coordinates go
in alongside an assembly id, and Mol\* generates the copies in the browser. A 60-mer
capsid therefore costs the same bytes as its asymmetric unit.

This is also why validation is independent of `--assembly`: symmetry copies introduce no
new residue numbers, so the addressable residue set is the deposited one either way.

## What the file does and does not carry

All the *data* is inline: coordinates, colors, tooltips, labels, and the state that ties
them together. There is no server side and no data fetch at view time.

Mol\* itself is loaded from a CDN, at a version pinned by the package. So viewing needs an
internet connection, but not a backend — which is what makes GitHub Pages, or any static
host, enough.
