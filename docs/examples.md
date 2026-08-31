# Examples

Each example is a directory under
[`examples/`](https://github.com/jbloomlab/prot-struct-viz/tree/main/examples) holding its
input files and a `spec.yaml`. The links for each example go to the directory that
produced it.

Every view carries its own caption, rendered from the Markdown file its `title_md` names.

## Antigenic regions of influenza H3 hemagglutinin

**Five views of one structure, each with its own CSV** saying how to color each site.
Switch between them with the **View** selector below the structure: only the first view
pins a camera, so whatever you frame there stays framed through the rest.

<!-- The src is a bare filename, not "examples/...", because MkDocs does not rewrite
     paths inside raw HTML the way it does Markdown links. This page is served at
     /examples/ and the rendered views land in the same directory, so they are
     siblings. The Markdown link below uses the source-relative path and is rewritten;
     keeping both means --strict still catches a missing render. -->
<iframe src="8faw_antigenic_regions.html" width="100%" height="900"
        style="border: 1px solid #ddd; border-radius: 4px;"
        title="Antigenic regions of influenza H3 hemagglutinin"></iframe>

[Open the above view on a new page](examples/8faw_antigenic_regions.html)

Rendered from
[`examples/8faw_antigenic_regions/`](https://github.com/jbloomlab/prot-struct-viz/tree/main/examples/8faw_antigenic_regions)
with:

```bash
prot-struct-viz spec.yaml
```

| file | what it is |
| --- | --- |
| [`spec.yaml`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/spec.yaml) | the whole input: five views sharing one YAML anchor |
| [`antigenic-regions-w-glycans.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/antigenic-regions-w-glycans.csv) | 499 rows: every modeled residue and every glycan, coloring antigenic regions |
| [`antigenic-regions.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/antigenic-regions.csv) | 493 rows: the same without the glycan rows, which is what lets this view's `glycans: hide` take them away |
| [`perth-2009-to-subclade-k.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/perth-2009-to-subclade-k.csv) | 45 rows: 40 sites to paint, as well as the sialic-acid receptor analogue. Everything unnamed falls back to `default_color` |
| [`2025-26-to-2026-27-vaccine.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/2025-26-to-2026-27-vaccine.csv) | 13 rows: a shorter list of sites |
| [`subclade-k-with-region-d-mutations.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/subclade-k-with-region-d-mutations.csv) | 15 rows: the 13 in the above view plus HA1 222 and 223 in a different color |
| [`antigenic-regions-w-glycans.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/antigenic-regions-w-glycans.md), [`antigenic-regions.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/antigenic-regions.md), [`perth-2009-to-subclade-k.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/perth-2009-to-subclade-k.md), [`2025-26-to-2026-27-vaccine.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/2025-26-to-2026-27-vaccine.md), [`subclade-k-with-region-d-mutations.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/subclade-k-with-region-d-mutations.md) | the caption for each view |
| [`make_coloring_csv.py`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/8faw_antigenic_regions/make_coloring_csv.py) | generates all five CSVs from a numbering map |

## Antigenic regions of influenza H1 hemagglutinin

**The same five views over the asymmetric unit rather than a biological assembly**: 9GSP
deposits all three protomers, so the asymmetric unit is already the trimer and there is no
symmetry for Mol\* to expand. Every CSV here therefore names each protomer in turn.

<!-- Bare filename in the iframe, source-relative path in the Markdown link — see the note
     on the first example for why the two differ. -->
<iframe src="9gsp_antigenic_regions.html" width="100%" height="900"
        style="border: 1px solid #ddd; border-radius: 4px;"
        title="Antigenic regions of influenza H1 hemagglutinin"></iframe>

[Open the above view on a new page](examples/9gsp_antigenic_regions.html)

Rendered from
[`examples/9gsp_antigenic_regions/`](https://github.com/jbloomlab/prot-struct-viz/tree/main/examples/9gsp_antigenic_regions)
with:

```bash
prot-struct-viz spec.yaml
```

| file | what it is |
| --- | --- |
| [`spec.yaml`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/spec.yaml) | the full input spec |
| [`antigenic-regions-w-glycans.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/antigenic-regions-w-glycans.csv) | 1491 rows: every modeled residue of all three protomers, and every glycan, coloring antigenic regions |
| [`antigenic-regions.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/antigenic-regions.csv) | 1464 rows: the same without the glycan rows, which is what lets this view's `glycans: hide` take them away |
| [`california-2009-to-d-3-1.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/california-2009-to-d-3-1.csv) | 111 rows: 37 sites to color, once per protomer. Everything unnamed falls back to `default_color` |
| [`d-3-1-to-d-3-1-1.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/d-3-1-to-d-3-1-1.csv) | 12 rows: 4 sites, once per protomer |
| [`d-3-1-1-with-g155e.csv`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/d-3-1-1-with-g155e.csv) | 15 rows: those 4 sites plus site 155 in a different color, again once per protomer |
| [`antigenic-regions-w-glycans.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/antigenic-regions-w-glycans.md), [`antigenic-regions.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/antigenic-regions.md), [`california-2009-to-d-3-1.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/california-2009-to-d-3-1.md), [`d-3-1-to-d-3-1-1.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/d-3-1-to-d-3-1-1.md), [`d-3-1-1-with-g155e.md`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/d-3-1-1-with-g155e.md) | the caption for each view |
| [`make_coloring_csv.py`](https://github.com/jbloomlab/prot-struct-viz/blob/main/examples/9gsp_antigenic_regions/make_coloring_csv.py) | generates all five CSVs |

## Influenza B neuraminidase active site

A handful of hand-picked residues instead: insertion-coded author numbering, a ligand and a
glycan colored from the CSV rather than by element, and a per-chain base representation. It
is also the one example that opens with Mol\*'s own panels showing, rather than closed.

<!-- Bare filename in the iframe, source-relative path in the Markdown link — see the note
     on the first example for why the two differ. -->
<iframe src="1f8b_active_site.html" width="100%" height="900"
        style="border: 1px solid #ddd; border-radius: 4px;"
        title="Influenza B neuraminidase active site"></iframe>

[Open the above view on a new page](examples/1f8b_active_site.html)

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
