# Rendering options

Everything on this page is a key in the [spec file](cli.md), which lists every key and
where it goes; this page explains what they mean together.

`structure`, `out`, `assembly` and `on_mismatch` are set once for the page, as are the two
presentation keys `viewer_height` and `molstar_ui`. Everything else is set per view, so two
views of one structure can differ in coloring, representation, labels, chains, which
heteroatoms they draw, and where the camera sits.

## Assemblies

`assembly` chooses what the browser shows:

| value | shows |
| --- | --- |
| `au` (default) | the deposited asymmetric unit, exactly as in the file |
| `1`, `2`, … | a biological assembly, using any id the entry defines |

A CSV row applies to **every symmetry copy** of the chain it names, so a residue
highlighted in one subunit is highlighted in all of them, and a persistent label is drawn
once per copy.

Validation always runs against the deposited chains, so it does not change with
`assembly`. A row naming a residue that exists in the entry but is not part of the
chosen assembly is reported separately rather than treated as a mismatch.

## Representations and heteroatoms

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
a failed run still leaves a record of what went wrong.

| mode | fatal when |
| --- | --- |
| `error-any` | the CSV or the structure has residues the other lacks |
| `error-extra-in-pdb` | the structure has residues the CSV omits |
| `error-extra-in-csv` | the CSV has rows with no matching residue |
| `report` | never; mismatches are reported and the run continues |

Waters are excluded from the addressable set — they would otherwise swamp the report — so
a CSV row landing on a water gets a message pointing at `waters` rather than a generic
"no such residue".

## Choosing what to draw

`chains` narrows a view to the chains you name. It is a display filter only:
validation still runs against every deposited chain, and rows for excluded chains are
reported as a separate warning rather than as mismatches.

`default_color` sets the color of every residue with no CSV row.

`title_md` renders a Markdown file into a caption below the viewer, which is where
a caption, a legend, or a link back to the source belongs. It sits under the structure so
the page opens on the view rather than on however many paragraphs the Markdown runs to.

## Getting the structure

`structure` takes either a PDB ID to fetch from RCSB, or a path to a local
`.cif`/`.pdb` file (`.gz` is decompressed transparently).

Downloads are **not** cached. Only the coordinate text is used, and it ends up embedded
in the output, so a cache would save one HTTP request at the price of a stale-file
failure mode. If you are re-rendering the same entry repeatedly, download it once and
pass the path.

## In the viewer

The generated page has its own controls below the structure, under the viewport that
holds Mol\*'s.

**View** appears when the spec lists more than one view, and switches which is on screen.
Every view is drawn when the page loads, so switching changes only what is visible: a site
you framed stays framed. Each view brings its own caption with it. The exception is a view
with its own `orientation`, which deliberately moves the camera — see
[Orientation](cli.md#orientation).

**Reset view** reloads the page as generated. It is there because of one limitation worth
knowing: the Mol\* Components panel stays live, but a representation you *add* from it
arrives in Mol\*'s default element coloring, not the CSV's, and there is no way to color
it from the UI. Mouseover tooltips and the persistent labels keep working on it; only the
color is missing. Reset view puts the original coloring and camera back.

**Labels** shows and hides the persistent on-structure labels. It appears only when the
CSV asked for at least one and the view could place it, and it moves all of them at once —
including the copy drawn on every symmetry mate under `assembly`. Mouseover tooltips are
separate and keep working while the labels are hidden.

See [How it works](internals.md#annotation-tables-not-baked-in-colors) for why, and for
what the entries in the Components panel are named after.

## The size of the viewer, and Mol\*'s panels

`viewer_height` sets how tall the viewer box is, as a CSS length; the width always fills
the page. The default `70vh` keeps a `30rem` floor so a short window cannot collapse it,
which only applies to viewport-relative units — an absolute height like `800px` is used
exactly as given.

`molstar_ui: hide` starts the page with Mol\*'s own panels closed: Structure Tools on the
right, the left panel, and the sequence strip along the top. They are closed, not removed —
the wrench in the viewport opens them, and it stays whatever this is set to. Useful when the
page is a figure first and a tool second.

One control we deliberately suppress: Mol\* renders a snapshot stepper in the top-left of
the viewport, which for these pages always reads `[1/1]` with a timestamp and a play button
that cycles a list of one. Views here are not MolViewSpec snapshots, so there is never
anything to step through, and Mol\* offers no option to turn it off — the generated page
hides it with a stylesheet rule.

## Saving an image

The page has no export button of its own: Mol\*'s is better. The camera icon in the
viewport opens a panel with a **Download** button and, above it, the settings that decide
what gets downloaded — resolution, transparent background, whether the orientation axes
are drawn, and the file format.

The resolution presets are Viewport, HD (1280 x 720), Full HD (1920 x 1080), Ultra HD
(3840 x 2160), 8K Ultra HD (7680 x 4320), and Custom. Custom runs from 128 px up to a
limit your GPU sets — half the smaller of its maximum texture and renderbuffer sizes,
which lands at 4096 or 8192 px per side on most machines; the panel's own slider shows
the real figure. Mol\* does not check the *presets* against that limit, so on hardware at
the lower end the 8K preset can fail where a custom size will not.

A large export is genuinely sharper rather than a blow-up of the viewport. Mol\* renders
it offscreen with settings the live view cannot afford: 16 jittered samples of
anti-aliasing against the viewport's 4, and, where ambient occlusion is on, 128 occlusion
samples against 32. Expect the render to take a few seconds at the larger sizes, and the
view to freeze while it does.

There is no ray tracing to turn on — Mol\* rasterizes, and its depth cues are screen-space
effects. The nearest thing is the optional **Global Illumination** pass (keyboard `G`),
which is off by default; a screenshot taken with it on runs it for more iterations than
the live view does.
