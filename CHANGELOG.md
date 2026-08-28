# Changelog

All notable changes to this project are documented here, in
[Keep a Changelog](https://keepachangelog.com/) format.

## [Unreleased]

### Added

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
- `--chains`, `--default-color`, `--default-representation`,
  `--chain-representation`, and `--title-md`.
- `prot_struct_viz.render()` as a Python API alongside the CLI, sharing one `ViewConfig`.
- Columns beyond the recognized ones are ignored, so a CSV can carry its own notes
  or numbering alongside the residue.
- The report names the files it wrote relative to the working directory when they
  are under it.
- Multiple colorings can be recorded as `color:<SchemeName>` CSV columns. All are parsed
  and reported; only the first is rendered so far.

### Fixed

- Persistent on-structure labels are drawn beside the residue they name. They previously
  collapsed onto a single point at the centre of the structure whenever `--assembly` was
  used, because Mol\*'s annotation labels derive one position from every atom a row
  matches, including every symmetry copy of it. Labels are now placed at explicit
  coordinates and replicated onto each symmetry copy.

### Changed

- The `--title-md` caption is rendered below the structure rather than above it, so the page
  opens on the view instead of on however many paragraphs the Markdown runs to.
- Documentation is single-sourced in `docs/`; the README is now a front door that links
  to it rather than a second copy that drifts from it.
- Examples live in `examples/<name>/` directories, each with the exact `command.sh` that
  produces it, and are rendered into the documentation site with the command and inputs
  shown alongside.

### Removed

- `--cache-dir` and the `cache_dir` argument to `render()`. Structures fetched from RCSB
  are no longer cached: only the coordinate text is ever used, so the cache bought one
  HTTP request in exchange for a stale-file failure mode. Pass a local file to
  `--structure` to render the same coordinates repeatedly.
