# Examples

Each example is a directory under
[`examples/`](https://github.com/jbloomlab/prot-struct-viz/tree/main/examples) holding its
input files and a `spec.yaml`. The links in each section go to the exact directory that
produced the view above them, so what is documented is what ran.

Every view carries its own caption, rendered from the Markdown file its `title_md`
names, which is where the structure and the color scheme are explained. This page only says what each example shows
you how to do.

Rebuild them all with `scripts/build_examples.sh`.

## Antigenic regions of influenza H3 hemagglutinin

**Four views of one structure, each with its own CSV**, which is what lets the last two
throw out the first two's coloring and paint only the sites that changed. Pick one from the
**View** selector below the structure: only the first view pins a camera, so whatever you
frame there stays framed through the rest. Display options are per view too — the first
draws the host glycans from its CSV, the other three set `glycans: hide`.

<!-- The src is a bare filename, not "examples/...", because MkDocs does not rewrite
     paths inside raw HTML the way it does Markdown links. This page is served at
     /examples/ and the rendered views land in the same directory, so they are
     siblings. The Markdown link below uses the source-relative path and is rewritten;
     keeping both means --strict still catches a missing render. -->
<iframe src="8faw_antigenic_regions.html" width="100%" height="900"
        style="border: 1px solid #ddd; border-radius: 4px;"
        title="Antigenic regions of influenza H3 hemagglutinin"></iframe>

[Open this view on its own](examples/8faw_antigenic_regions.html)

Rendered from
[`examples/8faw_antigenic_regions/`](https://github.com/jbloomlab/prot-struct-viz/tree/main/examples/8faw_antigenic_regions)
with:

```bash
prot-struct-viz spec.yaml
```

| file | what it is |
| --- | --- |
| [`spec.yaml`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/spec.yaml) | the whole input: four views sharing one YAML anchor |
| [`antigenic-regions-w-glycans.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/antigenic-regions-w-glycans.csv) | 499 rows: every modeled residue and every sugar |
| [`antigenic-regions.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/antigenic-regions.csv) | 493 rows: the same without the host-glycan rows, which is what lets that view's `glycans: hide` take them away |
| [`perth-2009-to-subclade-k.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/perth-2009-to-subclade-k.csv) | 45 rows: 40 sites to paint, and the receptor analogue it keeps. Everything unnamed falls back to `default_color` |
| [`2025-26-to-2026-27-vaccine.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/2025-26-to-2026-27-vaccine.csv) | 13 rows, the same shape over a shorter span |
| [`antigenic-regions-w-glycans.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/antigenic-regions-w-glycans.md), [`antigenic-regions.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/antigenic-regions.md), [`perth-2009-to-subclade-k.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/perth-2009-to-subclade-k.md), [`2025-26-to-2026-27-vaccine.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/2025-26-to-2026-27-vaccine.md) | the caption for each view — every input here is named after the view that reads it |
| [`make_coloring_csv.py`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/make_coloring_csv.py) | generates all four CSVs from a numbering map |

## Antigenic regions of influenza H1 hemagglutinin

The same job across a deposited assembly rather than a generated one: 9GSP contains all three
protomers, so the CSV annotates every one of them — 1491 rows and 150 drawn labels.

<!-- Bare filename in the iframe, source-relative path in the Markdown link — see the note
     on the first example for why the two differ. -->
<iframe src="9gsp_antigenic_regions.html" width="100%" height="900"
        style="border: 1px solid #ddd; border-radius: 4px;"
        title="Antigenic regions of influenza H1 hemagglutinin"></iframe>

[Open this view on its own](examples/9gsp_antigenic_regions.html)

Rendered from
[`examples/9gsp_antigenic_regions/`](https://github.com/jbloomlab/prot-struct-viz/tree/main/examples/9gsp_antigenic_regions)
with:

```bash
prot-struct-viz spec.yaml
```

| file | what it is |
| --- | --- |
| [`spec.yaml`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/spec.yaml) | the whole input: one view over the deposited trimer |
| [`coloring.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/coloring.csv) | 1491 rows across three chains; 150 ask for a drawn label |
| [`title.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/title.md) | the caption below the viewer |
| [`make_coloring_csv.py`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/make_coloring_csv.py) | generates `coloring.csv` from a numbering map |

## Influenza B neuraminidase active site

A handful of hand-picked residues instead: insertion-coded author numbering, a ligand and a
glycan colored from the CSV rather than by element, and a per-chain base representation. It
is also the one example that opens with Mol\*'s own panels showing, rather than closed.

<!-- Bare filename in the iframe, source-relative path in the Markdown link — see the note
     on the first example for why the two differ. -->
<iframe src="1f8b_active_site.html" width="100%" height="900"
        style="border: 1px solid #ddd; border-radius: 4px;"
        title="Influenza B neuraminidase active site"></iframe>

[Open this view on its own](examples/1f8b_active_site.html)

Rendered from
[`examples/1f8b_active_site/`](https://github.com/jbloomlab/prot-struct-viz/tree/main/examples/1f8b_active_site)
with:

```bash
prot-struct-viz spec.yaml
```

| file | what it is |
| --- | --- |
| [`spec.yaml`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/1f8b_active_site/spec.yaml) | the whole input: one view over the biological tetramer |
| [`coloring.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/1f8b_active_site/coloring.csv) | 19 hand-written rows; 6 ask for a drawn label. Its `notes` column shows how to keep an explanation beside a residue while `label` stays short enough to draw — unrecognized columns are ignored |
| [`chains.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/1f8b_active_site/chains.csv) | the per-chain base representations, for `chain_representation` |
| [`title.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/1f8b_active_site/title.md) | the caption below the viewer |
