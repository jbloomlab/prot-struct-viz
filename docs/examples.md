# Examples

Each example is a directory under
[`examples/`](https://github.com/jbloomlab/prot-struct-viz/tree/main/examples) holding its
input files and a `command.sh` — the exact invocation that produced the view below. The
command and the inputs shown on this page are *included* from those files rather than
retyped, so they cannot drift from what actually ran.

Rebuild them all with `scripts/build_examples.sh`.

## Influenza B neuraminidase active site

The sialic-acid analogue DANA bound in the active site of influenza B/Beijing/1/87
neuraminidase ([PDB 1F8B](https://www.rcsb.org/structure/1F8B)), shown as the biological
tetramer, with the residues that contact the inhibitor shaded by distance. Insertion-coded
sites (169A, 412A, 412B) are blue; the green sugar is a glycan named in the CSV, which
replaces its 3D-SNFG symbol with the CSV color while the other sugars keep theirs.

<!-- The src is a bare filename, not "examples/...", because MkDocs does not rewrite
     paths inside raw HTML the way it does Markdown links. This page is served at
     /examples/ and the rendered views land in the same directory, so they are
     siblings. The Markdown link below uses the source-relative path and is rewritten;
     keeping both means --strict still catches a missing render. -->
<iframe src="1f8b_active_site.html" width="100%" height="640"
        style="border: 1px solid #ddd; border-radius: 4px;"
        title="Influenza B neuraminidase active site"></iframe>

[Open this view on its own](examples/1f8b_active_site.html) — it is one 150 KB file with
no backend, exactly as produced.

### The command

```bash
--8<-- "examples/1f8b_active_site/command.sh"
```

### The CSV

Note the `notes` column: `prot-struct-viz` ignores columns it does not recognize, so the
explanation lives there while `label` stays short enough to draw into the 3D scene.

```csv
--8<-- "examples/1f8b_active_site/coloring.csv"
```

The run also uses [`chains.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/1f8b_active_site/chains.csv)
for `--chain-representation` and [`title.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/1f8b_active_site/title.md)
for the caption block above the viewer.

## Antigenic regions of influenza H3 hemagglutinin

Hemagglutinin from influenza A/Victoria/22/2020 (H3N2) with the alpha-2,6 receptor
analogue LSTc bound ([PDB 8FAW](https://www.rcsb.org/structure/8FAW)), shown as the
biological trimer. HA1 is colored by the classical antigenic region each site belongs to —
A red, B blue, C green, D purple, E orange — and every antigenic-site residue carries its
site number as a label drawn into the scene. Mousing over any residue gives its site in
HA1 or HA2 numbering, so the whole molecule is addressable, not just the colored parts.

This is the example that shows the package at scale: 493 CSV rows and 83 drawn labels,
against 19 and 6 for the neuraminidase view above.

<!-- Bare filename in the iframe, source-relative path in the Markdown link -- see the
     note on the first example for why the two differ. -->
<iframe src="8faw_antigenic_regions.html" width="100%" height="640"
        style="border: 1px solid #ddd; border-radius: 4px;"
        title="Antigenic regions of influenza H3 hemagglutinin"></iframe>

[Open this view on its own](examples/8faw_antigenic_regions.html)

### The command

```bash
--8<-- "examples/8faw_antigenic_regions/command.sh"
```

### The CSV

Too long to show whole, so this is the header plus the rows for antigenic site A. Rows are
sorted by chain then residue and HA1 starts at residue 11 on line 2, so HA1 residue `n` is
on line `n - 9`; site A spans residues 121 to 146, hence lines 112 to 137. Recompute those
bounds if the CSV is ever regenerated against a different structure.

```csv
--8<-- "examples/8faw_antigenic_regions/coloring.csv:1:1,112:137"
```

The remaining rows are the same shape: light gray with an `<n>_HA1` label for HA1 sites in
no antigenic region, mid gray with `<n>_HA2` for HA2, and five black rows for the LSTc
sugars, which are named in the CSV so they are drawn in that color instead of as 3D-SNFG
symbols. The host N-glycans are left out of the CSV and so keep their SNFG symbols.

Because those 493 rows are derived from two external sources — the
[H3N2 site numbering map](https://github.com/jbloomlab/flu-seqneut-2026/blob/main/data/nextstrain-prot-titers-tree_data/H3N2_site_numbering_map.tsv)
and Table 2 of [Stray & Pittman (2012)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3499391/) —
the derivation ships with them, in
[`make_coloring_csv.py`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/make_coloring_csv.py).
That script is run by hand, not by the build; `coloring.csv` is committed. It asserts the
numbering frame before writing, so a revised map or a different PDB entry fails loudly
rather than producing a shifted-by-one CSV.
[`title.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/title.md)
supplies the caption block above the viewer.
