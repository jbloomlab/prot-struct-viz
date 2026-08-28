# Examples

Each example is a directory under
[`examples/`](https://github.com/jbloomlab/prot-struct-viz/tree/main/examples) holding its
input files and a `command.sh` — the exact invocation that produced the view below. The
command and the inputs shown on this page are *included* from those files rather than
retyped, so they cannot drift from what actually ran.

Every view carries its own caption, rendered from that example's `title.md`, which is where
the structure and the color scheme are explained. This page only says what each example
shows you how to do.

Rebuild them all with `scripts/build_examples.sh`.

## Antigenic regions of influenza H3 hemagglutinin

Colors a whole molecule from a generated CSV — 499 rows, one per residue — with 83 of them
carrying a label drawn into the 3D scene.

<!-- The src is a bare filename, not "examples/...", because MkDocs does not rewrite
     paths inside raw HTML the way it does Markdown links. This page is served at
     /examples/ and the rendered views land in the same directory, so they are
     siblings. The Markdown link below uses the source-relative path and is rewritten;
     keeping both means --strict still catches a missing render. -->
<iframe src="8faw_antigenic_regions.html" width="100%" height="900"
        style="border: 1px solid #ddd; border-radius: 4px;"
        title="Antigenic regions of influenza H3 hemagglutinin"></iframe>

[Open this view on its own](examples/8faw_antigenic_regions.html)

### The command

```bash
--8<-- "examples/8faw_antigenic_regions/command.sh"
```

### The inputs

Far too long to show whole, so these are the rows for antigenic site A.

<!-- Rows are sorted by chain then residue and HA1 starts at residue 11 on line 2, so
     HA1 residue n is on line n - 9; site A is residues 121-146, hence lines 112-137.
     Recompute these bounds if coloring.csv is ever regenerated. -->
```csv
--8<-- "examples/8faw_antigenic_regions/coloring.csv:1:1,112:137"
```

[`title.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/title.md)
supplies the caption below the viewer.

## Antigenic regions of influenza H1 hemagglutinin

The same job across a deposited assembly rather than a generated one: 9GSP contains all three
protomers, so the CSV annotates every one of them — 1491 rows and 150 drawn labels.

<!-- Bare filename in the iframe, source-relative path in the Markdown link — see the note
     on the first example for why the two differ. -->
<iframe src="9gsp_antigenic_regions.html" width="100%" height="900"
        style="border: 1px solid #ddd; border-radius: 4px;"
        title="Antigenic regions of influenza H1 hemagglutinin"></iframe>

[Open this view on its own](examples/9gsp_antigenic_regions.html)

### The command

```bash
--8<-- "examples/9gsp_antigenic_regions/command.sh"
```

### The inputs

Far too long to show whole, so these are chain A's rows for antigenic site Sb.

<!-- Rows are sorted by chain then residue and chain A starts at residue 1 on line 2, so
     HA1 residue n is on line n + 1; site Sb is residues 184-195, hence lines 185-196.
     Recompute these bounds if coloring.csv is ever regenerated. -->
```csv
--8<-- "examples/9gsp_antigenic_regions/coloring.csv:1:1,185:196"
```

[`title.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/title.md)
supplies the caption below the viewer.

## Influenza B neuraminidase active site

A handful of hand-picked residues instead: insertion-coded author numbering, a ligand and a
glycan colored from the CSV rather than by element, and a per-chain base representation.

<!-- Bare filename in the iframe, source-relative path in the Markdown link — see the note
     on the first example for why the two differ. -->
<iframe src="1f8b_active_site.html" width="100%" height="900"
        style="border: 1px solid #ddd; border-radius: 4px;"
        title="Influenza B neuraminidase active site"></iframe>

[Open this view on its own](examples/1f8b_active_site.html)

### The command

```bash
--8<-- "examples/1f8b_active_site/command.sh"
```

### The inputs

Note the `notes` column: `prot-struct-viz` ignores columns it does not recognize, so the
explanation lives there while `label` stays short enough to draw into the 3D scene.

```csv
--8<-- "examples/1f8b_active_site/coloring.csv"
```

The run also uses [`chains.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/1f8b_active_site/chains.csv)
for `--chain-representation` and [`title.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/1f8b_active_site/title.md)
for the caption below the viewer.
