# Spec reference

The whole input is one YAML file:

```bash
prot-struct-viz spec.yaml
```

There are no other options. Everything is a key in the spec, which means a rendered
page has one reviewable, version-controllable description rather than a shell command
someone has to reconstruct.

Paths inside a spec — `csv`, `out`, `title_md`, `chain_representation` — resolve
relative to the spec file, not to the working directory. A spec and its inputs are a
directory you can move or copy.

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

## No defaults

**A view fills in nothing on your behalf.** Every key in the required list below must be
present in every view, or the spec is rejected naming what is missing. The point is that
a spec can be read on its own: what it says is what you get, with nothing to look up.

Repetition is removed with [YAML anchors](https://yaml.org/spec/1.2.2/#3222-anchors-and-aliases),
not with defaults — define the shared part once, merge it in with `<<:`, and override
per view as above. The top-level `definitions` key exists only to give an anchor
somewhere to live; the loader ignores it entirely.

The exception is keys whose absence is itself the answer: `chains` omitted means every
chain, `title_md` omitted means no caption, `chain_representation` omitted means no
per-chain overrides. There is nothing for you to state.

## Top-level keys

These four are required, alongside `views`.

| Key | Meaning |
| --- | --- |
| `structure` | PDB ID to fetch from RCSB, or path to a local `.cif`/`.pdb` file (`.gz` is decompressed). Downloads are not cached; see [How it works](internals.md#structures-are-not-cached). |
| `out` | Output HTML file. Must end in `.html`. The report is written beside it as `<stem>_report.txt`. |
| `assembly` | `au` for the deposited asymmetric unit, or an assembly id such as `"1"`. Quote it: YAML would otherwise read `1` as a number. See [Assemblies](#assemblies). |
| `on_mismatch` | What to do when a CSV's residue set and the structure's differ. See [Checking the CSV against the structure](#checking-the-csv-against-the-structure). |

`views` is a non-empty list, in the order the page offers them. The first is shown on
load. With one view the page renders no selector at all.

These two are optional, and describe the page rather than any view:

| Key | Meaning |
| --- | --- |
| `viewer_height` | Height of the viewer box as a CSS length — `px`, `rem`, `em`, `vh` or `%`. Default `70vh`. The width always fills the page. A `30rem` floor is added to viewport-relative heights, which are the ones a short window can collapse; an absolute height is taken exactly as written. |
| `molstar_ui` | `show` (default) or `hide`, for whether Mol\*'s own panels — Structure Tools, the left panel, and the sequence strip — start open. `hide` means closed, not gone: the wrench in the viewport still opens them. |

Both are about what the reader meets on the page, described in
[The rendered page](viewer.md). They have defaults where per-view keys do not, and the
distinction is deliberate: a view has to describe itself, because that is what makes a spec
readable on its own, while these describe the page and default to what the package did
before they existed.

## Per-view keys

Required in every view:

| Key | Meaning |
| --- | --- |
| `name` | Label for this view in the selector. Must be unique. |
| `csv` | Residue color/label/representation table for this view. See the [CSV schema](csv-schema.md). |
| `default_color` | Color for structure residues that have no CSV row. |
| `default_representation` | Base representation for the whole displayed polymer: `cartoon`, `ball-and-stick`, `spacefill`, `surface`, or `carbohydrate`. |
| `waters` | `show` or `hide`. Waters are not individually addressable from the CSV. |
| `ligands` | `show` or `hide` ligands not named in the CSV (element-colored ball-and-stick). |
| `glycans` | `snfg` or `hide` for glycans not named in the CSV. A glycan named in the CSV is never drawn as an SNFG symbol. |
| `ions` | `show` or `hide` ions not named in the CSV (element-colored spacefill). |

Optional, where leaving the key out says something:

| Key | Meaning |
| --- | --- |
| `chains` | Deposited chain IDs this view displays, as a list (`[A, B]`) or a comma-separated string. Omit to display every chain. It is a display filter only: validation still runs against every deposited chain, and rows for excluded chains are reported as a warning rather than as mismatches. |
| `chain_representation` | CSV with columns `chain,representation`, overriding the base representation for those chains. Omit for none. See below. |
| `title_md` | Markdown file rendered into a caption below the viewer, shown while this view is on screen — a legend, or a link back to the source. It sits *under* the structure so the page opens on the view rather than on however many paragraphs the Markdown runs to. Omit for no caption. |
| `orientation` | Where the camera sits for this view. Omit to leave the camera wherever the reader put it. See below. |

Everything above is per view, so two views of one structure can differ in coloring,
representation, labels, chains, which heteroatoms they draw, and where the camera sits.
Only `structure`, `out`, `assembly` and `on_mismatch` are shared: every view draws the same
molecule, in the same assembly, into the same page.

## Assemblies

`assembly` chooses what the browser shows:

| value | shows |
| --- | --- |
| `au` (default) | the deposited asymmetric unit, exactly as in the file |
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
`ball-and-stick`, `spacefill`, `surface`, and `carbohydrate`.

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

A view may pin its own camera. Switching to it then glides the camera there over about
400 ms; switching to a view *without* an `orientation` does not move the camera at all,
which is the default and the reason a view has to opt in.

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

`position` and `target` are required. `up` defaults to `[0, 1, 0]`, and omitting `radius`
leaves the zoom to Mol\*'s own fit of the scene. Nothing else belongs here — field of view,
clipping and the rest are properties of the scene, and pinning them in a spec only makes a
view behave oddly on a structure of a different size.

If the **first** view has an orientation it is also written into the MolViewSpec state, so
the page opens already framed rather than snapping into place after loading.

### Capturing one

You are not expected to write those numbers. Get them from a rendered page:

1. Render the spec with the view listed but no `orientation` yet.
2. Open the HTML and **add `#camera` to the end of the URL**, then reload. A **Copy
   camera** button appears next to *Reset view*.
3. Choose the view you are posing from the **View** selector, then rotate and zoom until
   it looks right.
4. Click **Copy camera**. The block is copied to your clipboard and also shown in a box
   below the controls, headed with the name of the view you are on.
5. Paste it into that view in the spec, and re-render.

`#camera` is a URL fragment, so it is never sent anywhere and works the same over
`file://`, a local server, or GitHub Pages. Nothing needs re-rendering to turn it on, and a
link you share does not carry it — readers never see the button.

The box matters as much as the clipboard: a rendered page is usually opened over `file://`,
which browsers do not treat as a secure context, so the clipboard API may be unavailable.
The button tries it, falls back, and shows the text either way; the status line says which
happened.

If you prefer the console, `psvCamera()` returns the same block, and
`viewer.plugin.canvas3d.camera.getSnapshot()` gives the raw camera.
