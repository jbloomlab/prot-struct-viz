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
