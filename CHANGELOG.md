# Changelog

All notable changes to this project are documented here, in
[Keep a Changelog](https://keepachangelog.com/) format.

## [Unreleased]

### Added

- `viewer_height`, setting how tall the viewer box is as a CSS length. The width still
  fills the page. Viewport-relative heights keep a `30rem` floor, which is the case a short
  window can collapse; an absolute height is used exactly as given.
- `molstar_ui`, for whether Mol\*'s own panels -- Structure Tools, the left panel, and the
  sequence strip -- start open. `hide` closes them without removing them: the wrench in the
  viewport still opens them, because it is gated by a different setting.
- A per-view `orientation`, pinning where the camera sits for that view. Switching to such a
  view glides the camera there; a view without one still leaves the camera untouched. Get
  the numbers by opening a rendered page with `#camera` appended to the URL, which reveals a
  **Copy camera** button -- so a published page never carries an authoring control, and
  capturing needs neither a re-render nor the browser console. `psvCamera()` returns the
  same block for anyone who prefers the console.
- Several named **views** of one structure in one page, each with its own CSV, colors,
  labels, representation, chains, heteroatom settings and caption. The page gets a
  **View** selector; every view is built when the page loads and switching only changes
  what is visible, so the camera does not move. Each view is its own MolViewSpec
  `structure` node, which is what keeps one view's tooltips out of another's.
- A **Labels** checkbox in the generated page, shown whenever the view drew at least one
  persistent on-structure label. It hides and shows all of them at once, including the copy
  on every symmetry mate, and leaves the mouseover tooltips alone. The labels are MolViewSpec
  primitives rather than Components-panel entries, so Mol\*'s own UI offers no way to switch
  them off.
- A **Reset view** button in the generated page, reloading the view as it was written.
  It exists because MolViewSpec attaches per-residue color to each representation it
  creates, so a representation added afterwards from Mol\*'s Components panel arrives in
  Mol\*'s default element coloring and cannot be recolored from the UI. Tooltips and
  labels attach to the structure and are unaffected.
- A second example, `8faw_antigenic_regions`: influenza H3 hemagglutinin with its receptor
  analogue bound (PDB 8FAW), as the biological trimer, with HA1 colored by classical
  antigenic region and every residue labeled with its HA1 or HA2 site number. At 499 CSV
  rows and 83 drawn labels it is the first example to exercise the package at the scale of
  a whole molecule rather than a handful of sites.
- A third example, `9gsp_antigenic_regions`: influenza H1 hemagglutinin, uncleaved (PDB
  9GSP), with HA1 colored by classical antigenic site from Table 2 of Wilson et al. 2015
  Virology 485:252-62. 9GSP deposits the whole trimer rather than one protomer, so its 1491
  CSV rows and 150 drawn labels cover three chains without any assembly being generated.
- Support for Python 3.14.
- `label_color` and `label_size` CSV columns styling the on-structure label text,
  defaulting to black and to a 2 A text height.
- Initial release. `prot-struct-viz` renders a protein structure to a self-contained
  static HTML Mol\* view, with per-residue colors, mouseover tooltips, persistent
  on-structure labels, and per-residue representations driven by a CSV.
- `--assembly` shows a biological assembly, generated in the browser from the embedded
  asymmetric unit rather than expanded on write.
- `--on-mismatch` checks the CSV residue set against the structure in four modes; a
  progress and mismatch report is written alongside the HTML in every mode.
- `--waters`, `--ligands`, `--glycans`, and `--ions` set the baseline appearance for
  heteroatoms the CSV does not name. A residue named in the CSV always takes the CSV's
  color and representation instead.
- `chains`, `default_color`, `default_representation`, `chain_representation`, and
  `title_md`.
- `prot_struct_viz.render()` as a Python API alongside the CLI, sharing one `ViewConfig`.
- Columns beyond the recognized ones are ignored, so a CSV can carry its own notes
  or numbering alongside the residue.
- The report names the files it wrote relative to the working directory when they
  are under it.

### Fixed

- The structure no longer shifts when you switch views. Captions were hidden with
  `display: none`, so a shorter one shortened the page: that scrolled it, and when it took
  the vertical scrollbar away the content box widened by the scrollbar width, resizing the
  Mol\* canvas sideways. Captions are now stacked in one grid cell and hidden with
  `visibility`, so the page height cannot change, and the scrollbar gutter is reserved
  either way. Measured on the H3 example: switching used to move the viewport 266 px
  vertically and 15 px horizontally, and now moves it not at all.
- Mol\*'s snapshot stepper is hidden. Views here are not MolViewSpec snapshots, so it always
  read `[1/1]` and a timestamp beside a play button that cycled a list of one. Mol\* offers
  no option to suppress it, so the page hides it with a stylesheet rule.
- The view selector is sized for the longest view name, so choosing a different view no
  longer widens it and shuffles the controls beside it.
- Persistent on-structure labels are drawn beside the residue they name. They previously
  collapsed onto a single point at the centre of the structure whenever `--assembly` was
  used, because Mol\*'s annotation labels derive one position from every atom a row
  matches, including every symmetry copy of it. Labels are now placed at explicit
  coordinates and replicated onto each symmetry copy.

### Changed

- **The whole input is now a single YAML spec file**, and the CLI is
  `prot-struct-viz spec.yaml` with no other options. Everything that was a flag is a key
  in that file, so a rendered page has one reviewable description rather than a shell
  command to reconstruct. The format fills in no defaults for a view: every view states
  its own options, and YAML anchors — with the ignored top-level `definitions` key to hold
  them — are how repetition is removed. Keys whose absence means something (`chains`,
  `title_md`, `chain_representation`) may still be omitted. Paths resolve relative to the
  spec file.
- `prot_struct_viz.render()` takes a `Spec` rather than positional arguments;
  `render_file()` and `load_spec()` are the file-based entry points.
- The generated page's own controls and the `title_md` caption are both rendered below the
  structure rather than above it, so the page opens on the view instead of on however many
  paragraphs the Markdown runs to.
- Documentation is single-sourced in `docs/`; the README is now a front door that links
  to it rather than a second copy that drifts from it.
- Examples live in `examples/<name>/` directories, each with the exact `spec.yaml` that
  produces it, and are rendered into the documentation site with the spec and inputs
  shown alongside. The H3 hemagglutinin example now has two views.

### Removed

- `color:<SchemeName>` CSV columns, and the `color` column is required again. Several
  colorings of one structure are now several CSVs, one per view — which also lets them
  differ in labels, representations and heteroatoms, not only in color.
- Every command-line flag, superseded by the spec file above.
- `--cache-dir` and the `cache_dir` argument to `render()`. Structures fetched from RCSB
  are no longer cached: only the coordinate text is ever used, so the cache bought one
  HTTP request in exchange for a stale-file failure mode. Pass a local file to
  `--structure` to render the same coordinates repeatedly.
