# Changelog

All notable changes to this project are documented here, in
[Keep a Changelog](https://keepachangelog.com/) format.

## [Unreleased]

### Fixed

- The opening view's camera is now the camera the spec asks for. MolViewSpec reads a
  `camera` node's position as a *reference* camera and scales its distance from the target
  by `1/(2*sin(fov/2))` -- about 1.31 at the default field of view -- so the page opened
  roughly a third further out than the numbers in the spec, and each round of **Copy
  camera** into the spec and back pushed it further out again. The page now re-applies the
  orientation itself after loading, through the same call every other view already used.
  Zoom is the distance between `position` and `target`; `radius` never controlled it, and
  the documentation said otherwise.
- `viewer_height` no longer has a `30rem` floor quietly overriding it. The floor guarded
  against a viewport-relative height collapsing on a short window, but it also meant any
  value below `30vh` rendered identically on a screen shorter than 1600px, so shortening
  the viewer in the spec appeared to do nothing.

### Added

- `viewer_height`, setting how tall the viewer box is as a CSS length. The width still
  fills the page. The value is used exactly as given.
- `molstar_ui`, for whether Mol\*'s own panels -- Structure Tools, the left panel, and the
  sequence strip -- start open. `hide` closes them without removing them: the wrench in the
  viewport still opens them, because it is gated by a different setting.
- A per-view `orientation`, pinning where the camera sits for that view. Switching to such a
  view glides the camera there; a view without one still leaves the camera untouched. Get
  the numbers by opening a rendered page with `#camera` appended to the URL, which reveals a
  **Copy camera** button -- so a published page never carries an authoring control, and
  capturing needs neither a re-render nor the browser console. `psvCamera()` returns the
  same block for anyone who prefers the console.
- Deep links to a view: the URL fragment `#view=<name>` opens the page on that view,
  framed and captioned, and switching views rewrites the fragment in place so sharing a
  view is copying the address bar. An unknown name falls back to the first view. Composes
  with the authoring fragment as `#view=<name>&camera`, and Back still leaves the page
  rather than walking the views.
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
- A **Reset view** button in the generated page, reloading the view as it was written,
  camera included -- the view you are on, not the first one.
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
  9GSP), with HA1 colored by classical antigenic region from Table 2 of Wilson et al. 2015
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

- The `8faw_antigenic_regions` example now has **five views** instead of two, and makes an
  argument rather than showing the same coloring twice: the classical antigenic regions of
  H3 HA1, the same with the host N-glycans hidden, then the sites that differ between
  A/Perth/16/2009 and subclade K, then the sites that differ between the 2025-2026 and
  2026-2027 vaccine strains, then that last comparison again with HA1 222 and 223 -- two
  antigenic region D sites in the 220-loop of the receptor-binding site -- picked out in the
  same purple the first two views give region D. 27 of the 40 modeled Perth-to-K
  substitutions, and 6 of the 8 modeled vaccine-update
  ones, land inside the antigenic regions the first two views draw.
  Each view names its own CSV, and its own `glycans` setting; the receptor analogue stays in
  all five because a residue named in the CSV is drawn whatever the heteroatom options say.
  Only the first view pins a camera, and no view draws labels into the scene any more, so
  that page has no **Labels** button -- the site or the substitution is a tooltip instead.
- The `9gsp_antigenic_regions` example is rebuilt on that same shape, with H1's own
  comparisons: the classical antigenic regions of H1 HA1, the same with the N-glycans
  hidden,
  then the sites that differ between A/California/07/2009 and subclade D.3.1
  (A/Missouri/11/2025), then the four that differ between D.3.1 and D.3.1.1
  (A/Andalucia/PMC-00977/2025), then that last comparison again with HA1 155 -- where G155E
  arises on the D.3.1.1 background -- picked out in the same indigo the first two views give
  antigenic region Sa. 12 of the 37 modeled 2009-to-D.3.1 substitutions, and 1 of the 4
  D.3.1-to-D.3.1.1 ones, land inside the antigenic regions the first two views draw. 9GSP
  deposits the whole trimer, so every CSV names all three protomers rather than relying on
  symmetry. Its drawn labels are gone too, so that page also has no **Labels** button.
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
  produces it, and are rendered into the documentation site. The H3 hemagglutinin example
  now has two views. Each documented example gives the command that made it and links its
  input files, rather than inlining every `spec.yaml` and slabs of every CSV -- the page
  was mostly verbatim input, and a reader had to scroll a YAML file to reach the next
  structure.
- Two of the three examples now open with Mol\*'s own panels closed, so they read as
  figures; the influenza B neuraminidase one still opens with them showing, so the site
  shows both states.
- **Documentation reorganized so each key is described exactly once**, in the order a user
  meets it: examples, then the spec reference, then the CSV schema. The "Rendering options"
  page is gone -- what a key *means* (assemblies, representation layers, heteroatom
  precedence, `on_mismatch`) is now in the spec reference beside the key itself, and what a
  reader of the output can click is a new, short **The rendered page**. Implementation
  detail that had accumulated in user-facing prose -- screenshot sample counts, GPU export
  limits, why the snapshot stepper is hidden, why downloads are not cached -- moved to
  **How it works**.
- The spec reference moved from `docs/cli.md` to `docs/spec.md`, so its published URL is
  now `/spec/` rather than `/cli/`. The page has documented the YAML spec rather than a CLI
  since the flags went away.

### Removed

- `color:<SchemeName>` CSV columns, and the `color` column is required again. Several
  colorings of one structure are now several CSVs, one per view — which also lets them
  differ in labels, representations and heteroatoms, not only in color.
- Every command-line flag, superseded by the spec file above.
- `--cache-dir` and the `cache_dir` argument to `render()`. Structures fetched from RCSB
  are no longer cached: only the coordinate text is ever used, so the cache bought one
  HTTP request in exchange for a stale-file failure mode. Pass a local file as
  `structure` to render the same coordinates repeatedly.
