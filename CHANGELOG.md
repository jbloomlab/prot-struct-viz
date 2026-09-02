# Changelog

All notable changes to this project are documented here, in
[Keep a Changelog](https://keepachangelog.com/) format.

## [0.3.0] - 2026-09-02

### Added

- `gaussian-surface` as a representation, wherever a representation can be named. It is
  the smoother Gaussian surface; `surface` keeps meaning the solvent-excluded molecular
  one, so no existing spec changes meaning, and a view may use both at once.
- An optional top-level `style` key, `default` or `illustrative`. `illustrative` renders
  the page with Mol\*'s flat unlit shading, silhouette outlines and ambient occlusion. It
  changes no color: per-residue coloring still comes from the CSV.

## [0.2.0] - 2026-09-02

### Added

- `--out PATH` on the CLI, and an `out` argument on `render_file` and `load_spec`, naming
  the output HTML file. Unlike the spec's own `out`, it resolves relative to the working
  directory, so a build system that owns the output tree does not need a path out of the
  spec's directory written into the spec. The report follows it as `<stem>_report.txt`.

### Changed

- The output path must be given exactly once, either as the spec's `out` key or as
  `--out`: giving both, or neither, is an error. A spec that names its own `out` is
  unaffected.

## [0.1.0] - 2026-08-31

### Added

- First release. `prot-struct-viz spec.yaml` renders a protein structure to a
  self-contained static HTML [Mol\*](https://molstar.org/) page: coordinates, colors,
  tooltips, labels and the viewer state all travel in the one file, so it can be dropped
  on GitHub Pages with no backend.
- A CSV drives per-residue color, mouseover tooltip, persistent on-structure label
  (with its own color and size), and an additional representation layered over the base
  one. Author numbering throughout, insertion codes included. Columns the package does
  not recognize are ignored, so a CSV can carry its own notes.
- A spec may hold several named **views** of one structure, each with its own CSV,
  colors, chains, representations, heteroatom settings, caption and camera. The page
  gets a selector; every view is built on load, so switching does not move the camera.
  `#view=<slug>` in the URL opens the page on one particular view.
- `assembly` shows a biological assembly, generated in the browser from the embedded
  asymmetric unit, so a high-symmetry entry costs no more bytes than its AU.
- `on_mismatch` checks each CSV's residue set against the structure in four modes. A
  progress log and mismatch report is written beside the HTML in every mode, including
  the fatal ones.
- The rendered page carries a **Labels** toggle, a **Reset view** button, and — with
  `#camera` appended to the URL — a **Copy camera** button that writes an `orientation`
  block for the spec.
- `prot_struct_viz.render()` as a Python API alongside the CLI, taking the same `Spec`
  the YAML file parses to.
