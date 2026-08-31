# Changelog

All notable changes to this project are documented here, in
[Keep a Changelog](https://keepachangelog.com/) format.

## [Unreleased]

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
