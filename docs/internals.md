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
*initial* state, not a frozen picture. The Components panel stays fully usable, so a
reader of your figure can change representations and colorings live, add a
representation you did not think of, or turn off the one you did.

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
