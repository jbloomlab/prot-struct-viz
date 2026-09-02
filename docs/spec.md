# Spec reference

The whole input is one YAML file:

```bash
prot-struct-viz spec.yaml
```

Paths inside a spec (`csv`, `title_md`, `chain_representation`, and a local
`structure`) resolve relative to the spec file, not to the working directory, making a
spec and its inputs a directory you can move or copy. The output path is the exception,
and may instead be given on the command line: see
[Where the page is written](#where-the-page-is-written).

## Shape

```yaml
structure: 8FAW                 # shared by every view
out: ha.html
assembly: "1"
on_mismatch: error-extra-in-csv

definitions:                    # ignored; holds YAML anchors
  base: &base
    default_color: "#d9d9d9"
    waters: hide
    ligands: show
    glycans: snfg
    ions: show

views:
  - <<: *base
    name: Antigenic regions
    csv: coloring.csv
    default_representation: surface
    title_md: antigenic.md
  - <<: *base
    name: Fold and receptor
    csv: coloring.csv
    default_representation: cartoon
```

## Use YAML anchors for repeated elements

Most keys do not have defaults. Instead repetition is removed with
[YAML anchors](https://yaml.org/spec/1.2.2/#3222-anchors-and-aliases): define the shared
part once, merge it in with `<<:`, and override per view as above. The top-level
`definitions` key exists only to give an anchor somewhere to live; the loader ignores it
entirely.

The exception is keys whose absence is itself the answer: `chains` omitted means every
chain, `title_md` omitted means no caption, `chain_representation` omitted means no
per-chain overrides.

## Top-level keys

Required keys, alongside `views` and the output path
([below](#where-the-page-is-written)).

| Key | Meaning |
| --- | --- |
| `structure` | PDB ID to fetch from RCSB, or path to a local `.cif`/`.pdb` file (`.gz` is decompressed). |
| `assembly` | `au` for the deposited asymmetric unit, or an assembly id such as `"1"`. Quote it: YAML would otherwise read `1` as a number. See [Assemblies](#assemblies). |
| `on_mismatch` | What to do when a CSV's residue set and the structure's differ. See [Checking the CSV against the structure](#checking-the-csv-against-the-structure). |

`views` is a non-empty list of views, in the order the rendered page offers them. The
first is shown on load. With one view the page renders no selector at all.

There are three optional top-level keys:

| Key | Meaning |
| --- | --- |
| `viewer_height` | Height of the viewer box as a CSS length — `px`, `rem`, `em`, `vh` or `%`. Default `70vh`. The width always fills the page. The value is used exactly as written, so a viewport-relative height gives a short viewer on a short window. |
| `molstar_ui` | `show` (default) or `hide`, for whether Mol\*'s own panels (Structure Tools, the left panel, and the sequence strip) start open or closed. Either way, the wrench in the viewport toggles them, so `hide` means closed, not unavailable. |
| `style` | `default` (default) or `illustrative`, for how the page is shaded: `illustrative` is Mol\*'s own flat unlit shading with silhouette outlines and ambient occlusion. It changes no color — every color still comes from the CSV — and it suits a surface or spacefill base more than a cartoon one. It applies to the whole page rather than to one view. |

## Where the page is written

The output path can be specified either in the YAML or as a command-line argument:

| source | resolved relative to |
| --- | --- |
| the spec's `out` key | the spec file |
| `--out PATH` on the command line | the working directory |

Exactly one of the two must be given: both is an error naming both values, and neither is
an error asking for one.

```bash
prot-struct-viz --out results/prot-struct-viz/ha.html spec.yaml
```

Either way the path must end in `.html`, and the report is written beside it as
`<stem>_report.txt`.

## Per-view keys

Required in every view:

| Key | Meaning |
| --- | --- |
| `name` | Label for this view in the selector. Must be unique. |
| `csv` | Residue color/label/representation table for this view. See the [CSV schema](csv-schema.md). |
| `default_color` | Color for structure residues that have no CSV row. Hex or a CSS color name, same as the CSV's `color` column. |
| `default_representation` | Base representation for the whole displayed polymer: `cartoon`, `ball-and-stick`, `spacefill`, `surface`, `gaussian-surface`, or `carbohydrate`. |
| `waters` | `show` or `hide`. Waters are not individually addressable from the CSV. |
| `ligands` | `show` or `hide` ligands not named in the CSV (element-colored ball-and-stick). |
| `glycans` | `snfg` or `hide` for glycans not named in the CSV. A glycan named in the CSV is never drawn as an SNFG symbol. |
| `ions` | `show` or `hide` ions not named in the CSV (element-colored spacefill). |

Optional keys for every view:

| Key | Meaning |
| --- | --- |
| `chains` | Deposited chain IDs this view displays, as a list (`[A, B]`) or a comma-separated string. Omit to display every chain. It is a display filter only: validation still runs against every deposited chain, and rows for excluded chains are reported as a warning rather than as mismatches. |
| `chain_representation` | CSV with columns `chain,representation`, overriding the base representation for those chains. Omit for none. See below. |
| `title_md` | Markdown file rendered into a caption below the viewer, shown while this view is on screen. Omit for no caption. |
| `orientation` | Initial orientation of the structure. See below for how to get your desired orientation. |

## Assemblies

`assembly` chooses what the browser shows:

| value | shows |
| --- | --- |
| `au` | the deposited asymmetric unit, exactly as in the file |
| `1`, `2`, … | a biological assembly, using any id the entry defines |

A CSV row applies to **every symmetry copy** of the chain it names, so a residue
highlighted in one subunit is highlighted in all of them, and a persistent label is drawn
once per copy. Assemblies are generated by Mol\* in the browser rather than expanded into
the file, which is also why validation does not change with `assembly` — a row naming a
residue that exists in the entry but is not part of the chosen assembly is reported
separately rather than treated as a mismatch.

## Representation layers and heteroatoms

The representation of a residue is built in three layers:

1. `default_representation` sets the global base.
2. `chain_representation` overrides that base for whole chains.
3. The CSV's `representation` column is **added on top**, per residue.

The third layer being additive is what produces the standard figure: a cartoon backbone
with sticks on a handful of key residues. Allowed values at every layer are `cartoon`,
`ball-and-stick`, `spacefill`, `surface`, `gaussian-surface`, and `carbohydrate`.

`surface` is the solvent-excluded molecular surface and `gaussian-surface` the smoother
Gaussian one, which usually reads better over a whole assembly. They are separate values,
so one view can use both — on different chains, or one added over the other.

`chain_representation` takes a small CSV:

```csv
chain,representation
A,cartoon
B,surface
```

This sets the base for each chain's **polymer** only. A CSV-named ligand or ion on that
chain still gets ball-and-stick, because a cartoon or a surface draws nothing for a
single heteroatom residue.

`waters`, `ligands`, `glycans`, and `ions` set the **baseline** appearance for
heteroatoms the CSV does not name: ligands and ions element-colored, glycans as 3D-SNFG
symbols.

**A residue named in the CSV always wins.** Naming a glycan gives it the CSV color and
representation instead of its SNFG symbol — a recolored SNFG symbol would be meaningless
— and naming a ligand replaces element coloring with the flat CSV color. Sugars and
ligands the CSV does not mention keep their standard appearance, so the two color
languages never fight over the same atoms.

## Checking the CSV against the structure

`on_mismatch` decides what happens when the CSV and the structure disagree about which
residues exist. A report file is written in **every** mode, including the fatal ones, so
a failed run still leaves a record of what went wrong. Every view is checked, and any one
of them can fail the run.

| mode | fatal when |
| --- | --- |
| `error-any` | the CSV or the structure has residues the other lacks |
| `error-extra-in-pdb` | the structure has residues the CSV omits |
| `error-extra-in-csv` | the CSV has rows with no matching residue |
| `report` | never; mismatches are reported and the run continues |

Waters are excluded from the addressable set — they would otherwise swamp the report — so
a CSV row landing on a water gets a message pointing at `waters` rather than a generic
"no such residue".

## Orientation

A view may pin its own camera orientation with the `orientation` key. Switching to it
then glides the camera to that orientation; switching to a view *without* an
`orientation` does not move the camera at all.

```yaml
views:
  - <<: *base
    name: Receptor site
    csv: coloring.csv
    orientation:
      position: [11.2, -48.6, 187.3]
      target: [-0.4, -57.4, 13.8]
      up: [0, 1, 0]
      radius: 76.1
```

`position` and `target` are required; `up` defaults to `[0, 1, 0]`, and `radius` may be
omitted.

You are not expected to write out the `orientation` by hand. Instead, get it from a
rendered page after moving the structure to the orientation you want:

1. Render the spec with the view listed but no `orientation` yet.
2. Open the HTML and **add `#camera` to the end of the URL**, then reload. A **Copy
   camera** button appears next to *Reset view*. If the URL already has a `#` because it
   names a view, add `&camera` after it (`#view=<slug>&camera`).
3. Select the view you are posing, then rotate and zoom with the mouse until it looks
   right.
4. Click **Copy camera**. The block is copied to your clipboard and also shown in a box
   below the controls, headed with the name of the view you are on.
5. Paste it into that view in the spec, and re-render to get the orientation you captured.

If you prefer the console, `psvCamera()` returns the same block, and
`viewer.plugin.canvas3d.camera.getSnapshot()` gives the raw camera.
