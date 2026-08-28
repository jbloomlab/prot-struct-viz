"""Build the MolViewSpec state and render it into a self-contained HTML file.

The output HTML embeds a base64-encoded **MVSX** archive: a zip holding the MVS
state (``index.mvsj``), the deposited coordinates, and one JSON annotation table
per view. Relative URIs inside an MVSX resolve to members of the archive, so the
whole page travels in a single file with no external data fetches.

A page can hold several **views** of one structure -- different colourings,
labels, representations, and heteroatom choices. Each gets its own MVS
``structure`` node, hanging off the one shared parse, because Mol* collects
tooltips per structure node: separate nodes are what keeps one view's tooltips,
labels and colours from leaking into another's. Each node carries a ``ref``, which
Mol* turns into a cell tag, and that is how the page finds a view to show or
hide it.

Two things are deliberate here:

* **Assemblies are not expanded.** Only the deposited coordinates are embedded,
  plus an assembly id; Mol* generates the symmetry copies in the browser, which
  keeps the file small for high-symmetry entries.
* **The CSV always wins over the default heteroatom appearance.** Rows for
  CSV-named heteroatoms are given a ``base_rep`` and never a ``het_layer``, so
  they are physically absent from the default ligand/glycan/ion components. The
  override is a property of how the annotation table is built, not of the order
  in which nodes are applied.
"""

from __future__ import annotations

import base64
import dataclasses
import io
import json
import pathlib
import zipfile

import jinja2
import markdown_it
from molviewspec import create_builder

from ._config import (
    DEFAULT_LABEL_COLOR,
    DEFAULT_LABEL_SIZE,
    HETERO_CSV_REPRESENTATION,
    REPRESENTATIONS,
    InputError,
    ViewConfig,
)
from .residues import ColoringData, ResidueKey, ResidueSpec, split_residue
from .structure import ResidueClass, addressable_residues

#: Mol* version loaded from the CDN. Bumping this is a one-line change here; the
#: MVS API changes between versions, so check the state still loads afterwards.
MOLSTAR_VERSION = "5.11.0"

#: Member names inside the MVSX archive.
STATE_MEMBER = "index.mvsj"


def annotation_member(slug: str) -> str:
    """Archive member holding one view's annotation table."""
    return f"annotations/{slug}.json"


def view_ref(slug: str) -> str:
    """MVS ``ref`` for a view's structure node.

    Mol* exposes this as the cell tag ``mvs-ref:<ref>``, which the page resolves
    with ``PluginExtensions.mvs.util.queryMVSRef`` to find the subtree to toggle.
    """
    return f"view:{slug}"


#: Representation used for each class of heteroatom the CSV does not name.
HETERO_LAYER_REPRESENTATIONS = {
    "ligand": "ball_and_stick",
    "glycan": "carbohydrate",
    "ion": "spacefill",
    "water": "ball_and_stick",
}

#: Camera-facing offset, in Angstroms, so label text floats in front of the residue
#: it names rather than sitting inside it.
LABEL_OFFSET = 1.0

_TEMPLATE_DIR = pathlib.Path(__file__).parent / "templates"


def _archive_uri(member: str) -> str:
    """A URI relative to the MVSX archive root."""
    return f"./{member}"


def build_annotations(
    coloring: ColoringData,
    deposited: dict[ResidueKey, ResidueClass],
    config: ViewConfig,
    chain_representations: dict[str, str],
) -> list[dict]:
    """Build the JSON annotation table, one row per displayed residue that needs one.

    Every row carries the three selector fields (``auth_asym_id``,
    ``auth_seq_id``, ``pdbx_PDB_ins_code``) plus whichever dependent fields
    apply. ``pdbx_PDB_ins_code`` is always written, empty string included,
    because MVS treats a missing selector field as "matches anything" -- omitting
    it would make a row for residue 412 also colour 412A and 412B.

    Parameters
    ----------
    coloring
        The parsed CSV. Rows naming residues absent from ``deposited`` are
        dropped; validation has already reported them.
    deposited
        Displayed residues and their classes. Already restricted to
        ``chains``, which is what confines every component to those chains.
    config
        The view options.
    chain_representations
        Per-chain base representation overrides.

    Returns
    -------
    list of dict
        JSON-able annotation rows.
    """
    addressable = addressable_residues(deposited)
    by_key = {spec.key: spec for spec in coloring.specs if spec.key in addressable}

    rows = []
    for key in sorted(deposited, key=lambda k: (k[0], split_residue(k[1]))):
        chain, residue = key
        residue_class = deposited[key]
        number, ins_code = split_residue(residue)
        spec = by_key.get(key)

        fields: dict[str, str] = {}
        if spec is not None:
            fields["color"] = spec.color
            if spec.label is not None:
                fields["tooltip"] = spec.label
            if spec.representation is not None:
                fields["extra_rep"] = REPRESENTATIONS[spec.representation]

        if residue_class == "polymer":
            base = chain_representations.get(chain, config.default_representation)
            fields["base_rep"] = REPRESENTATIONS[base]
        elif spec is not None:
            # A CSV-named heteroatom. Polymer representations (cartoon by default)
            # draw nothing for a ligand or ion, so it always gets ball-and-stick as
            # its base -- including when chain_representation names its chain,
            # since that setting is about the chain's polymer. Anything in the row's
            # representation column still applies additively on top.
            fields["base_rep"] = REPRESENTATIONS[HETERO_CSV_REPRESENTATION]
        else:
            layer = _default_layer(residue_class, config)
            if layer is not None:
                fields["het_layer"] = layer

        if not fields:
            continue  # nothing to say about this residue
        rows.append(
            {
                "auth_asym_id": chain,
                "auth_seq_id": number,
                "pdbx_PDB_ins_code": ins_code,
                **fields,
            }
        )
    return rows


def _default_layer(residue_class: ResidueClass, config: ViewConfig) -> str | None:
    """The default heteroatom layer for a residue the CSV does not name."""
    visible = {
        "ligand": config.ligands == "show",
        "glycan": config.glycans == "snfg",
        "ion": config.ions == "show",
        "water": config.waters == "show",
    }
    if residue_class in visible and visible[residue_class]:
        return residue_class
    return None


def _distinct(rows: list[dict], field: str) -> list[str]:
    """Distinct values of a field, in first-appearance order."""
    seen = []
    for row in rows:
        value = row.get(field)
        if value is not None and value not in seen:
            seen.append(value)
    return seen


def build_label_primitives(
    structure,
    coloring: ColoringData,
    deposited: dict[ResidueKey, ResidueClass],
    centroids: dict[ResidueKey, tuple[float, float, float]],
    instance_groups: list[tuple[set[str], list[list[float]]]],
) -> list[ResidueKey]:
    """Attach persistent 3D labels as MolViewSpec primitives at explicit positions.

    ``label_from_uri`` cannot be used for this: it derives a label's position from
    the boundary sphere of *every* atom the annotation row matches, and a row
    without ``instance_id`` matches its residue in every symmetry copy, so under an
    assembly the label lands in the middle of the whole thing. Primitives take
    explicit coordinates, and are also the only MVS label node that accepts a
    per-label colour and size.

    Each primitives group carries the assembly transforms that apply to its chains,
    which is what puts a copy of the label on every symmetry copy.

    Returns
    -------
    list
        Keys that were asked for a label but could not be placed, for the caller to
        report. A label is unplaceable if the residue is absent from the displayed
        chains, has no heavy atoms, or falls under no assembly generator.
    """
    wanted = [
        spec
        for spec in coloring.specs
        if spec.show_label and spec.key in deposited and spec.key in centroids
    ]
    unplaced = [
        spec.key
        for spec in coloring.specs
        if spec.show_label and (spec.key not in deposited or spec.key not in centroids)
    ]
    if not wanted:
        return unplaced

    # One group per set of transforms, so a label is only replicated by operators
    # that actually apply to its chain. "au" has no transforms, hence one group.
    groups: list[tuple[list[list[float]] | None, list[ResidueSpec]]] = []
    if not instance_groups:
        groups.append((None, wanted))
    else:
        placed = set()
        for chains, matrices in instance_groups:
            members = [spec for spec in wanted if spec.chain in chains]
            if members:
                groups.append((matrices, members))
                placed.update(spec.key for spec in members)
        unplaced.extend(spec.key for spec in wanted if spec.key not in placed)

    for matrices, members in groups:
        primitives = structure.primitives(
            label_color=DEFAULT_LABEL_COLOR,
            **({"instances": matrices} if matrices is not None else {}),
        )
        for spec in members:
            primitives.label(
                position=centroids[spec.key],
                text=spec.label,
                label_color=spec.label_color or DEFAULT_LABEL_COLOR,
                label_size=(
                    spec.label_size
                    if spec.label_size is not None
                    else DEFAULT_LABEL_SIZE
                ),
                label_offset=LABEL_OFFSET,
            )
    return unplaced


@dataclasses.dataclass(frozen=True)
class ViewBuild:
    """Everything needed to draw one view into the shared MVS state."""

    slug: str
    config: ViewConfig
    rows: list[dict]
    labels: tuple | None = None
    orientation: dict | None = None


def build_state(
    builds: list[ViewBuild], fmt: str, structure_member: str
) -> tuple[dict, dict[str, list[ResidueKey]]]:
    """Build the MolViewSpec state drawing every view.

    The coordinates are downloaded and parsed once; each view then gets its own
    ``structure`` node under that parse. Sharing the parse is what keeps the file
    from carrying the structure more than once; not sharing the structure node is
    what keeps the views independent, since Mol* attaches tooltips per structure.

    Parameters
    ----------
    builds
        One `ViewBuild` per view, in the order the page offers them.
    fmt
        ``"mmcif"`` or ``"pdb"``.
    structure_member
        Name of the coordinate file inside the MVSX archive.

    Returns
    -------
    tuple
        The JSON-able MVS state, and per view slug the label keys that could not
        be placed.
    """
    builder = create_builder()

    # MVS has exactly one camera -- the node is root-level and the loader keeps the
    # last one it sees -- so only the view the page opens on can be expressed here.
    # Every other view's orientation is applied by the page when you switch to it.
    #
    # This node is a first paint, not the final camera. MolViewSpec reads its
    # position as a *reference* camera, one that just fits a sphere of radius
    # |position - target| / 2, and multiplies the distance to the target by
    # 1/(2*sin(fov/2)) -- about 1.31 at the default 45 degrees. Emitting it opens
    # the page facing the right way instead of on Mol*'s default fit of the scene;
    # the page then re-applies the same orientation through setSnapshot, which
    # copies the position verbatim and is what the reader ends up looking at. The
    # node also cannot carry `radius`: MVS camera params are target, position, up
    # and near, so Orientation.radius reaches only the page's ORIENTATIONS array.
    opening = builds[0].orientation if builds else None
    if opening is not None:
        builder.camera(
            target=opening["target"],
            position=opening["position"],
            up=opening["up"],
        )

    parsed = builder.download(url=_archive_uri(structure_member)).parse(format=fmt)

    unplaced: dict[str, list[ResidueKey]] = {}
    for build in builds:
        config = build.config
        ref = view_ref(build.slug)
        if config.assembly == "au":
            structure = parsed.model_structure(ref=ref)
        else:
            structure = parsed.assembly_structure(assembly_id=config.assembly, ref=ref)

        annotation = {
            "uri": _archive_uri(annotation_member(build.slug)),
            "format": "json",
            "schema": "auth_residue",
        }
        rows = build.rows
        has_color = any("color" in row for row in rows)

        def _styled(component, representation_type, has_color=has_color):
            representation = component.representation(type=representation_type)
            representation.color(color=config.default_color)
            if has_color:
                representation.color_from_uri(**annotation, field_name="color")
            return representation

        # Base representation, one component per distinct value.
        for value in _distinct(rows, "base_rep"):
            component = structure.component_from_uri(
                **annotation, field_name="base_rep", field_values=[value]
            )
            _styled(component, value)

        # Additive per-residue overrides from the CSV's representation column.
        for value in _distinct(rows, "extra_rep"):
            component = structure.component_from_uri(
                **annotation, field_name="extra_rep", field_values=[value]
            )
            _styled(component, value)

        # Default heteroatom layers. These deliberately get no color node, so they
        # keep Mol*'s element coloring and 3D-SNFG sugar colors.
        for value in _distinct(rows, "het_layer"):
            component = structure.component_from_uri(
                **annotation, field_name="het_layer", field_values=[value]
            )
            component.representation(type=HETERO_LAYER_REPRESENTATIONS[value])

        if any("tooltip" in row for row in rows):
            structure.tooltip_from_uri(**annotation, field_name="tooltip")

        unplaced[build.slug] = (
            build_label_primitives(structure, *build.labels)
            if build.labels is not None
            else []
        )

    return json.loads(builder.get_state().dumps()), unplaced


def build_mvsx(
    state: dict,
    coordinate_text: str,
    structure_member: str,
    rows_by_slug: dict[str, list[dict]],
) -> bytes:
    """Zip the state, the coordinates, and every view's annotations into an MVSX.

    The coordinates go in once however many views there are; only the annotation
    tables are per view.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(STATE_MEMBER, json.dumps(state))
        archive.writestr(structure_member, coordinate_text)
        for slug, rows in rows_by_slug.items():
            archive.writestr(annotation_member(slug), json.dumps(rows))
    return buffer.getvalue()


def render_title(title_md: pathlib.Path | None) -> str:
    """Render the optional Markdown title file to an HTML fragment."""
    if title_md is None:
        return ""
    path = pathlib.Path(title_md)
    if not path.is_file():
        raise InputError(f"no such file: {path}")
    return markdown_it.MarkdownIt().render(path.read_text(encoding="utf-8"))


def render_html(
    mvsx: bytes,
    views: list[dict],
    page_title: str,
    show_label_toggle: bool,
    viewer_height: str = "70vh",
    molstar_ui: str = "show",
) -> str:
    """Render the viewer template around a base64 MVSX payload.

    Parameters
    ----------
    mvsx
        The archive, embedded base64 in a non-executing script block.
    views
        One dict per view, in page order, with ``name``, ``slug``, ``caption``
        (an HTML fragment, possibly empty) and ``orientation`` (a camera snapshot
        or ``None``). The first is shown on load; the selector is rendered only
        when there is more than one.
    page_title
        The HTML ``<title>``.
    show_label_toggle
        Renders the Labels checkbox. It is the caller's job to pass ``False``
        when no view drew a persistent label: a checkbox that moves nothing is
        worse than no checkbox.
    viewer_height
        CSS length for the viewer box. The width always fills the page.
    molstar_ui
        ``"show"`` or ``"hide"``: whether Mol*'s own panels start open.
    """
    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(_TEMPLATE_DIR),
        autoescape=jinja2.select_autoescape(["html"]),
        undefined=jinja2.StrictUndefined,
    )
    template = environment.get_template("viewer.html.jinja")
    return template.render(
        molstar_version=MOLSTAR_VERSION,
        mvsx_base64=base64.b64encode(mvsx).decode("ascii"),
        views=views,  # captions are already HTML; the template marks them safe
        page_title=page_title,
        show_label_toggle=show_label_toggle,
        viewer_height=viewer_height,
        molstar_ui_shown=molstar_ui == "show",
        # An empty #header collapses to nothing via :empty, which stops a page with
        # no captions from carrying a blank band under the structure.
        has_captions=any(view["caption"] for view in views),
        select_width=max((len(view["name"]) for view in views), default=0),
    )
