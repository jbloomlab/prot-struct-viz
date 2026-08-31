# Instructions for Claude Code

## Bloom lab coding standards

@bloomlab-coding-standards/CLAUDE.md

The [standards](https://github.com/jbloomlab/bloomlab-coding-standards) are pinned at a
commit of that submodule; update periodically with
`git submodule update --remote bloomlab-coding-standards`.

## Project conventions

- **Pure-Python package** managed with `pyproject.toml` and a plain `venv`, not conda.
  `pyproject.toml` is the single source of truth for dependencies, the supported Python
  version, and tool settings — do not restate any of them in prose.
  ```bash
  python3 -m venv .venv && .venv/bin/pip install -e ".[dev,docs]"
  ```
  The `src/` layout needs `dev-mode-dirs = ["src"]` for editable installs to work.
- **One input: the YAML spec.** `prot-struct-viz spec.yaml` is the whole CLI; there are
  no flags. `spec.load_spec` parses it into a `Spec` of `View`s, each a name, a CSV, and a
  `ViewConfig`, and `render(spec)` takes it from there. Every option is described once in
  `_config.OPTION_DOCS`, whose keys are also the spec's keys and `ViewConfig`'s field
  names. Adding an option means a `ViewConfig` field, an `OPTION_DOCS` entry, and a row in
  `docs/spec.md` — never a second description. `tests/test_docs.py` checks that every
  `OPTION_DOCS` key reaches the reference page.
- **The spec format has no defaults, on purpose.** Every per-view key must be stated, so a
  spec is readable without knowing what the package would have filled in; YAML anchors are
  how repetition is removed, and the ignored top-level `definitions` key is where they
  live. The exception is keys whose absence is the answer (`chains`, `title_md`,
  `chain_representation`). `ViewConfig` keeps Python-side defaults for programmatic use --
  the strictness belongs to the loader, not the dataclass.
- **A view is one MVS `structure` node, not one component.** Views share the `download`
  and `parse` nodes and nothing below them, because Mol\* collects `tooltip_from_uri` per
  structure node -- one shared node would merge every view's tooltips into one mouseover.
  Each structure node carries `ref="view:<slug>"`, which Mol\* exposes as the cell tag
  `mvs-ref:view:<slug>`; the page resolves it with
  `PluginExtensions.mvs.util.queryMVSRef` and walks the subtree to show or hide it.
  MolViewSpec has no way to mark a node hidden on load, so the initial hide is done in JS
  after the load, alongside the Labels checkbox and under one combined rule.
- **The URL fragment is one shared namespace with a grammar.** `#` then
  `&`-separated tokens: `view=<slug>` picks a view, `camera` reveals the authoring
  button, and unknown tokens are ignored. Parse it with the page's `fragment()`; do not
  compare `location.hash` to a literal, and do not claim `#` for anything that is not a
  token. The page writes the fragment back with `history.replaceState` so Back keeps
  leaving the page, and because replaceState fires no `hashchange` the listener needs no
  guard against the page's own writes.
- **Allowed values live in `_config.py`.** `REPRESENTATIONS`, `MISMATCH_MODES`, and the
  heteroatom flag choices are defined once and imported by the parser, the CLI, and the
  renderer. Do not restate a set of allowed values anywhere else.
- **Docstring style is NumPy** (Parameters / Returns with the `----------` underline), to
  match `mkdocs.yml`'s `docstring_style: numpy`.
- **Author numbering throughout.** Residues are keyed `(auth_asym_id, "<num><icode>")`
  with the insertion code inside the string, and are read from CSVs as strings so `0169`
  never becomes `169`. Anything user-facing speaks author numbering.
- **Fail fast at the boundary.** Bad input raises `InputError` naming the line and
  column; the CLI turns that into a message and a non-zero exit, never a traceback.
  Analysis code downstream may then assume its inputs are good.
- **Scratch files are ignored as `/_*`, anchored to the repository root** so Python's own
  underscore-prefixed modules stay tracked. A bare `_*` would silently untrack
  `__init__.py`.
- **Record user-facing changes in `CHANGELOG.md`** under `## [Unreleased]` as you make
  them, in [Keep a Changelog](https://keepachangelog.com/) format.
- **`docs/` is the single source; `README.md` is a front door.** New reference material
  goes in `docs/` and is linked from the README, never written into both. The two prose
  copies that preceded this rule had already drifted in four places.
- **Escape `Mol\*` in every Markdown file.** Python-Markdown -- unlike CommonMark, whose
  flanking rules reject it -- pairs a bare `Mol*` with the next `*` in the same paragraph
  and silently italicizes the wrong span. `tests/test_docs.py` enforces this.
- **Test the docs mechanically, never editorially.** A check in `tests/test_docs.py` earns
  its place only if it catches a *silent* breakage that nothing else already enforces --
  the `Mol\*` escape, a `blob/main/` link to a path that no longer exists, an
  `OPTION_DOCS` key that never reached `docs/spec.md`. Never assert that a particular
  sentence, link or count is present: that pins an editorial choice, so shortening a page
  fails a test with nothing actually wrong. A negative control belongs on the regex, with
  a synthetic string -- not on the live prose. Anchors are `mkdocs build --strict`'s job
  via `validation.links.anchors`, which resolves them from the rendered HTML and so covers
  the mkdocstrings headings a hand-rolled slugify cannot see.
- **Examples are spec-driven directories**: `examples/<name>/` holds the inputs plus
  `spec.yaml`, the literal input. `docs/examples.md` gives the command and *links* the
  input files rather than inlining them -- inlining made the page mostly verbatim YAML and
  CSV -- and `tests/test_docs.py` checks every linked example path exists, so a renamed
  input fails a test instead of shipping a 404. A spec's `out` is part of the spec, so
  `scripts/build_examples.sh` renders each one unchanged into `examples/output/` and
  *copies* to another destination rather than overriding it. The rendered HTML is generated
  into a gitignored `docs/examples/` and must be built before `mkdocs` -- both
  `scripts/build_docs.sh` and `.github/workflows/docs.yml` do this. Adding an example is a
  new directory plus a section in `docs/examples.md`.
- **A `docs/examples.md` section says what the example demonstrates about the package, not
  what the structure is.** Each rendered view already embeds the Markdown file its
  `title_md` names as a caption, so a structure description, color key or assembly note
  written onto the page is shown twice a few hundred pixels apart and has to be maintained
  in both places. Keep the section to one framing sentence, the command, and the table of
  linked inputs.
- **In a multi-view example, a view's CSV and caption are named after the view**, by the
  same `spec._slug` the page uses for its option values -- `antigenic-regions.csv` and
  `antigenic-regions.md` for a view named `antigenic regions`. With several views in one
  directory, `coloring.csv` and `title.md` stop saying which view they belong to.
  `tests/test_residues.py` enforces it, and skips single-view examples, which have nothing
  to disambiguate.
- **MVS color is per representation; tooltips and labels are not.** `color_from_uri` is a
  child of each `representation` node, so a representation the user adds from Mol\*'s
  Components panel arrives uncolored and cannot be colored from the UI -- MolViewSpec has
  no structure-level or global color node. `tooltip_from_uri` and the label primitives
  attach to the structure and do survive. The template's **Reset view** button reloads the
  state from the payload still in the DOM, which is the only way back. Do not describe the
  Mol\* UI as freely editable without this caveat; `docs/internals.md` once did.
- **Releases are tag-driven.** Push a `v*` tag matching `pyproject.toml`'s `version` and
  `release.yml` publishes to PyPI by trusted publishing (OIDC, no stored token). The
  recipe is in that workflow's header comment.
- **Structures fetched from RCSB are not cached**, deliberately: only the coordinate text
  is used, so a cache bought one HTTP request in exchange for a stale-file failure mode.
  A local path as `structure` is the escape hatch. Relatedly, never put
  `show_default=True` on a click option whose default is home-relative -- `mkdocs-click`
  would bake the docs builder's `$HOME` into the published CLI reference.

## Mol\* / MolViewSpec (read this before writing any viewer code)

- **Pinned Mol\* version: 5.11.0**, declared once as `viewer.MOLSTAR_VERSION` and loaded
  from the jsDelivr CDN by the template. Do not mix versions. Bump it to the latest
  release periodically, and re-run the verification below afterwards — the MVS API does
  change between versions.
- **Wrapper choice: the plain Mol\* `Viewer` app plus MVS built with the `molviewspec`
  Python package.** Neither pdbe-molstar nor rcsb-molstar is used: `Viewer.loadMvsData`
  accepts a base64 MVSX archive, which covers the self-contained-file requirement, and
  MVS covers all the annotation work. Reach for a wrapper only if a feature genuinely
  cannot be expressed in MVS.
- **`molviewspec` lags Mol\*.** It accepts fewer representation types than Mol\* can draw
  (no `backbone`, `line`, `putty`). Offer only what it validates; if the project needs
  one of the others, open an issue on `molstar/mol-view-spec` rather than emitting a
  state that fails validation.
- **Docs over memory.** Before writing or editing viewer code, read the docs for the
  pinned version; if a doc and your prior knowledge disagree, the doc wins. Start at
  molstar.org and navigate to the current plugin/viewer and MolViewSpec docs rather than
  hard-coding deep links (page paths rot). Also consult the molstar/molstar GitHub repo
  — its `CHANGELOG.md` is the fastest way to spot API changes at the pinned version, and
  `src/examples/` has working embed code.
- **MVS is the annotation path.** Do color / label / tooltip / component work through the
  MolViewSpec annotation system, not hand-written overpaint.
- **A missing MVS selector field matches anything.** Always write
  `pdbx_PDB_ins_code` explicitly, empty string included: a row for residue 412 that
  omits it also selects 412A and 412B. The same trap applies to any selector field.
- **`label_from_uri` cannot label individual residues.** It derives one position per
  label group from the boundary sphere of *every* atom the row matches, and a row
  without `instance_id` matches its residue in every symmetry copy, so under an assembly
  every label collapses onto the centre of the structure. It also takes no colour or size
  parameters. Persistent labels are therefore MVS **label primitives** at explicit
  coordinates, replicated across symmetry by the primitives group's `instances`
  matrices. Tooltips are unaffected and stay on `tooltip_from_uri`.
- **Layering is structural, not ordinal.** "The CSV wins over the default heteroatom
  appearance" is true because CSV-named residues are never given a `het_layer` value, so
  they are absent from those components. Do not reimplement it as node ordering.

## Verifying viewer changes

Mol\* code is easy to write so that it looks right and silently does nothing, so after
any change to `viewer.py` or the template:

0. `scripts/build_examples.sh`, then look at the report it writes. A state that renders
   nothing still exits zero, so the report's residue counts are the first sanity check.
1. `scripts/check.sh`. The test suite validates generated states against the MVS schema
   with `molviewspec.validate_state_tree` and asserts every annotation row lands in some
   component — which catches a state that would render blank.
2. Validate with Mol\*'s own tooling, which is stricter than the Python schema check.
   Extract the MVSX from the HTML (`<script id="mvsx-payload">`, base64) and:
   ```bash
   ml nodejs/20.13.1-GCCcore-13.3.0
   npx -p molstar@5.11.0 mvs-validate index.mvsj
   ```
   `npx -p molstar@5.11.0 mvs-render -i view.mvsx -o out.png` renders offscreen and is
   the strongest headless check, but its `gl` dependency needs X11 development headers
   that the cluster does not have. Do not report it as passing when it could not run.
3. To check that annotation rows resolve to the residues intended, without a GPU, drive
   Mol\*'s own selection code in Node: `getAtomRangesForRow` from
   `molstar/lib/commonjs/extensions/mvs/helpers/selections` with `IndicesAndSortings`
   from `.../helpers/indexing`. This is how the insertion-code behavior above was
   established.
4. **Open the HTML in a browser** and confirm coloring, mouseover tooltips, persistent
   labels, the assembly, SNFG glycans, and image download from Mol\*'s own camera panel
   actually work. This cannot be done from a non-interactive shell: generate the example,
   say what to look at, and report that this step is the user's.
