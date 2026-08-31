"""Tests for the annotation table, the MVS state, and the HTML output."""

import base64
import dataclasses
import io
import json
import re
import zipfile

import pytest

from prot_struct_viz import ViewConfig, render
from prot_struct_viz._config import InputError
from prot_struct_viz.residues import parse_csv
from prot_struct_viz.structure import assembly_instance_transforms, residue_centroids
from prot_struct_viz.viewer import (
    MOLSTAR_VERSION,
    STATE_MEMBER,
    ViewBuild,
    annotation_member,
    build_annotations,
    build_mvsx,
    build_state,
    view_ref,
)

#: Slug of the single view the state helpers below build.
SLUG = "main"


def _build(rows, config=None, labels=None, slug=SLUG):
    return ViewBuild(slug=slug, config=config or ViewConfig(), rows=rows, labels=labels)


def _embedded_state(html):
    """The MVS state out of a rendered page's base64 MVSX payload."""
    payload = re.search(
        r'<script id="mvsx-payload" type="text/plain">(.*?)</script>', html, re.S
    ).group(1)
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(payload.strip()))) as zf:
        return json.loads(zf.read(STATE_MEMBER))


def _state(rows, config=None, labels=None):
    """build_state's state, dropping the unplaced-label list the callers ignore."""
    state, _ = build_state([_build(rows, config, labels)], "mmcif", "structure.cif")
    return state


def _walk(node, out=None):
    """Every node in the state tree."""
    out = [] if out is None else out
    out.append(node)
    for child in node.get("children") or []:
        _walk(child, out)
    return out


def _labels(state):
    """Label primitives as ``text -> params``."""
    return {
        n["params"]["text"]: n["params"]
        for n in _walk(state["root"])
        if n["kind"] == "primitive" and n["params"].get("kind") == "label"
    }


def _primitive_groups(state):
    return [n for n in _walk(state["root"]) if n["kind"] == "primitives"]


CSV = """chain,residue,color,label,show_label,representation
A,412,#2ca02c,plain 412,,
A,412A,#d62728,site 412A,True,ball-and-stick
A,412B,#ff7f0e,site 412B,,
A,0,#9467bd,the DANA ligand,,
A,998,#8c564b,a calcium,,spacefill
B,1,#e377c2,a glycan,,ball-and-stick
"""


@pytest.fixture
def coloring(write_csv):
    return parse_csv(write_csv(CSV))


@pytest.fixture
def rows(coloring, deposited):
    return build_annotations(coloring, deposited, ViewConfig(), {})


def _with_title(spec, title_md):
    """The same spec with a caption on its first view."""
    return dataclasses.replace(
        spec,
        views=(dataclasses.replace(spec.views[0], title_md=title_md), *spec.views[1:]),
    )


def _row(rows, chain, seq_id, ins_code=""):
    matches = [
        r
        for r in rows
        if r["auth_asym_id"] == chain
        and r["auth_seq_id"] == seq_id
        and r["pdbx_PDB_ins_code"] == ins_code
    ]
    assert len(matches) == 1, f"expected one row for {chain}/{seq_id}{ins_code}"
    return matches[0]


def test_every_row_carries_an_explicit_ins_code(rows):
    """MVS treats a missing selector field as 'matches anything', so a row for
    residue 412 with no ins_code would also colour 412A and 412B."""
    for row in rows:
        assert "pdbx_PDB_ins_code" in row
        assert isinstance(row["pdbx_PDB_ins_code"], str)


def test_insertion_codes_are_separate_rows(rows):
    assert _row(rows, "A", 412)["color"] == "#2ca02c"
    assert _row(rows, "A", 412, "A")["color"] == "#d62728"
    assert _row(rows, "A", 412, "B")["color"] == "#ff7f0e"


def test_polymer_gets_the_base_representation(rows):
    assert _row(rows, "A", 100)["base_rep"] == "cartoon"


def test_csv_named_heteroatom_is_not_drawn_as_cartoon(rows):
    """cartoon draws nothing for a ligand, so a CSV-named one falls back."""
    assert _row(rows, "A", 0)["base_rep"] == "ball_and_stick"
    assert _row(rows, "B", 1)["base_rep"] == "ball_and_stick"


def test_csv_named_heteroatoms_leave_the_default_layers(rows):
    """The whole point of 'the CSV always wins' over --ligands/--glycans/--ions."""
    for chain, seq_id in [("A", 0), ("A", 998), ("B", 1)]:
        assert "het_layer" not in _row(rows, chain, seq_id)
    layers = {
        (r["auth_asym_id"], r["auth_seq_id"]): r["het_layer"]
        for r in rows
        if "het_layer" in r
    }
    assert ("A", 0) not in layers  # the only ligand, and the CSV named it
    assert layers[("A", 999)] == "ion"  # the calcium the CSV did not name
    assert ("A", 998) not in layers
    assert layers[("B", 2)] == "glycan"


def test_unnamed_heteroatoms_keep_their_default_layer(rows):
    assert _row(rows, "A", 999)["het_layer"] == "ion"
    assert "color" not in _row(rows, "A", 999)


def test_waters_hidden_by_default(rows, deposited):
    waters = {k for k, v in deposited.items() if v == "water"}
    assert waters
    keyed = {(r["auth_asym_id"], str(r["auth_seq_id"])) for r in rows}
    assert not (waters & keyed)


def test_waters_shown_when_asked(coloring, deposited):
    rows = build_annotations(coloring, deposited, ViewConfig(waters="show"), {})
    layers = {r["het_layer"] for r in rows if "het_layer" in r}
    assert "water" in layers


def test_hiding_a_class_drops_its_layer(coloring, deposited):
    config = ViewConfig(glycans="hide", ions="hide", ligands="hide")
    rows = build_annotations(coloring, deposited, config, {})
    layers = {r["het_layer"] for r in rows if "het_layer" in r}
    assert layers == set()


def test_tooltips_are_annotation_fields(rows):
    assert _row(rows, "A", 412, "A")["tooltip"] == "site 412A"
    assert _row(rows, "A", 412)["tooltip"] == "plain 412"
    # Persistent labels are primitives, not annotation fields.
    for row in rows:
        assert "label" not in row


def test_additive_representation_is_separate_from_base(rows):
    calcium = _row(rows, "A", 998)
    assert calcium["base_rep"] == "ball_and_stick"
    assert calcium["extra_rep"] == "spacefill"


def test_per_chain_representation_override(coloring, deposited):
    rows = build_annotations(coloring, deposited, ViewConfig(), {"A": "surface"})
    assert _row(rows, "A", 100)["base_rep"] == "surface"


def test_chain_subset_confines_the_annotation_table(coloring, structure):
    from prot_struct_viz.structure import get_deposited_residues

    subset = get_deposited_residues(structure, ["B"])
    rows = build_annotations(coloring, subset, ViewConfig(), {})
    assert {r["auth_asym_id"] for r in rows} == {"B"}


def test_rows_with_nothing_to_say_are_omitted(coloring, deposited):
    """A hidden water needs no row, so it gets none."""
    rows = build_annotations(coloring, deposited, ViewConfig(waters="hide"), {})
    for row in rows:
        assert set(row) > {"auth_asym_id", "auth_seq_id", "pdbx_PDB_ins_code"}


def test_csv_rows_absent_from_the_structure_are_dropped(write_csv, deposited):
    coloring = parse_csv(write_csv("chain,residue,color\nZ,1,red\nA,100,blue\n"))
    rows = build_annotations(coloring, deposited, ViewConfig(), {})
    assert not [r for r in rows if r["auth_asym_id"] == "Z"]
    assert _row(rows, "A", 100)["color"] == "#0000ff"


def _components(state, field_name):
    """Values selected by component_from_uri nodes on a given field."""
    found = {}

    def walk(node):
        params = node.get("params") or {}
        if (
            node["kind"] == "component_from_uri"
            and params.get("field_name") == field_name
        ):
            for value in params["field_values"]:
                found[value] = node.get("children") or []
        for child in node.get("children") or []:
            walk(child)

    walk(state["root"])
    return found


def _find(state, kind):
    for node in _walk(state["root"]):
        if node["kind"] == kind:
            return node
    return None


def test_state_uses_the_assembly_when_asked(rows):
    state = _state(rows, ViewConfig(assembly="1"))
    structure_node = _find(state, "structure")
    assert structure_node["params"]["type"] == "assembly"
    assert structure_node["params"]["assembly_id"] == "1"


def test_state_uses_the_deposited_model_for_au(rows):
    assert _find(_state(rows), "structure")["params"]["type"] == "model"


def test_state_colors_base_components_but_not_hetero_layers(rows):
    state = _state(rows, ViewConfig())

    for children in _components(state, "base_rep").values():
        representation = children[0]
        kinds = {c["kind"] for c in representation.get("children") or []}
        # Default color first, CSV colors layered on top.
        assert kinds == {"color", "color_from_uri"}

    for children in _components(state, "het_layer").values():
        representation = children[0]
        # No color node: keeps element coloring and 3D-SNFG sugar colors.
        assert not (representation.get("children") or [])


def test_glycan_layer_uses_the_carbohydrate_representation(rows):
    state = _state(rows, ViewConfig())
    layers = _components(state, "het_layer")
    assert layers["glycan"][0]["params"]["type"] == "carbohydrate"
    assert layers["ion"][0]["params"]["type"] == "spacefill"


def test_state_adds_a_tooltip_node(rows):
    kinds = {n["kind"] for n in _walk(_state(rows)["root"])}
    assert "tooltip_from_uri" in kinds
    # label_from_uri cannot position a per-residue label under an assembly, so it
    # is not used at all; see test_labels_are_placed_on_their_own_residues.
    assert "label_from_uri" not in kinds


def test_no_tooltip_node_without_tooltips(write_csv, deposited):
    coloring = parse_csv(write_csv("chain,residue,color\nA,100,red\n"))
    rows = build_annotations(coloring, deposited, ViewConfig(), {})
    kinds = {n["kind"] for n in _walk(_state(rows)["root"])}
    assert "tooltip_from_uri" not in kinds


def test_mvsx_archive_members(rows, coordinate_text):
    state = _state(rows, ViewConfig())
    archive = build_mvsx(state, coordinate_text, "structure.cif", {SLUG: rows})
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        assert set(zf.namelist()) == {
            STATE_MEMBER,
            "structure.cif",
            annotation_member(SLUG),
        }
        assert json.loads(zf.read(annotation_member(SLUG))) == rows
        assert zf.read("structure.cif").decode() == coordinate_text


def test_views_share_the_coordinates_and_not_the_annotations(rows, coordinate_text):
    """The structure is embedded once however many views there are."""
    builds = [_build(rows, slug="one"), _build(rows, slug="two")]
    state, _ = build_state(builds, "mmcif", "structure.cif")
    archive = build_mvsx(
        state, coordinate_text, "structure.cif", {"one": rows, "two": rows}
    )
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        assert set(zf.namelist()) == {
            STATE_MEMBER,
            "structure.cif",
            annotation_member("one"),
            annotation_member("two"),
        }


def test_each_view_gets_its_own_structure_node(rows):
    """Mol* collects tooltips per structure node, so views must not share one.

    One shared node would merge every view's tooltips into one mouseover.
    """
    state, _ = build_state(
        [_build(rows, slug="one"), _build(rows, slug="two")],
        "mmcif",
        "structure.cif",
    )
    structures = [n for n in _walk(state["root"]) if n["kind"] == "structure"]
    assert [n.get("ref") for n in structures] == [view_ref("one"), view_ref("two")]
    assert len([n for n in _walk(state["root"]) if n["kind"] == "parse"]) == 1
    for node in structures:
        kinds = {child["kind"] for child in node["children"]}
        assert "tooltip_from_uri" in kinds


def test_each_view_reads_its_own_annotation_member(rows):
    state, _ = build_state(
        [_build(rows, slug="one"), _build(rows, slug="two")],
        "mmcif",
        "structure.cif",
    )
    uris = {
        n["params"]["uri"]
        for n in _walk(state["root"])
        if n["kind"] in ("component_from_uri", "color_from_uri", "tooltip_from_uri")
    }
    assert uris == {
        f"./{annotation_member('one')}",
        f"./{annotation_member('two')}",
    }


def test_page_refs_are_the_refs_in_the_state(tmp_path, write_csv, make_spec):
    """The page finds a view's subtree by ref, so a mismatch hides every view.

    Nothing else catches it: queryMVSRef returning nothing only logs a warning,
    and the page then renders with every subtree left visible.
    """
    out = tmp_path / "view.html"
    csv = write_csv(CSV)
    render(make_spec([("First", csv), ("Second", csv)], out))
    html = out.read_text()

    page_refs = json.loads(re.search(r"var REFS = (\[.*?\]);", html).group(1))
    state = _embedded_state(html)
    state_refs = [
        n.get("ref") for n in _walk(state["root"]) if n["kind"] == "structure"
    ]
    assert page_refs == state_refs == [view_ref("first"), view_ref("second")]


def test_render_writes_html_and_report(tmp_path, write_csv, make_spec):
    out = tmp_path / "view.html"
    render(make_spec([("Main", write_csv(CSV))], out))
    assert out.is_file()
    assert (tmp_path / "view_report.txt").is_file()

    html = out.read_text()
    assert f"molstar@{MOLSTAR_VERSION}/build/viewer/molstar.js" in html
    assert "loadMvsData('base64,' + payload, 'mvsx')" in html
    # Mol*'s own UI stays enabled so the view can be re-styled interactively.
    assert "layoutShowControls: true" in html
    # Reset view is the only way back from a UI-added representation, which MVS
    # cannot color. It reloads the embedded payload, so the two go together.
    assert 'id="reset-view"' in html
    assert 'id="mvsx-payload"' in html
    # The two APIs the Labels checkbox is built on: it finds the label
    # representations by object type, then hides them. Lose either in a template edit
    # and the checkbox still renders but moves nothing, which is how it shipped broken
    # the first time.
    assert "PSO.Shape.Representation3D.is(cell.obj)" in html
    assert "updateCellState" in html
    # How the page finds a view's subtree: the MVS ref becomes a cell tag, and
    # this is the exported API that resolves it. Without it nothing can be shown
    # or hidden at all, not even in the single-view case.
    assert "queryMVSRef" in html


def test_controls_and_caption_sit_below_the_viewer(tmp_path, write_csv, make_spec):
    """The page should open on the structure, not on what surrounds it."""
    title = tmp_path / "title.md"
    title.write_text("# Neuraminidase\n")
    out = tmp_path / "view.html"
    spec = make_spec([("Main", write_csv(CSV))], out)
    spec = _with_title(spec, title)
    render(spec)
    html = out.read_text()
    assert (
        html.index('id="viewer"')
        < html.index('id="controls"')
        < html.index('id="header"')
    )


def test_label_toggle_appears_only_when_labels_are_drawn(
    tmp_path, write_csv, make_spec
):
    """A checkbox that would move nothing is worse than no checkbox."""
    labelled = tmp_path / "labelled.html"
    render(make_spec([("Main", write_csv(CSV))], labelled))
    assert 'id="label-toggle"' in labelled.read_text()

    # Same rows, but nothing asks for a persistent label.
    plain = tmp_path / "plain.html"
    render(
        make_spec(
            [("Main", write_csv(CSV.replace(",True,", ",,"), name="plain.csv"))],
            plain,
        )
    )
    assert 'id="label-toggle"' not in plain.read_text()


def test_view_selector_appears_only_with_more_than_one_view(
    tmp_path, write_csv, make_spec
):
    """A selector offering one choice is furniture, not a control."""
    csv = write_csv(CSV)
    one = tmp_path / "one.html"
    render(make_spec([("Only", csv)], one))
    assert 'id="view-select"' not in one.read_text()

    two = tmp_path / "two.html"
    render(make_spec([("First", csv), ("Second", csv)], two))
    html = two.read_text()
    assert 'id="view-select"' in html
    assert '<option value="first">First</option>' in html
    assert '<option value="second">Second</option>' in html


def test_each_view_gets_a_caption_and_only_the_first_is_shown(
    tmp_path, write_csv, make_spec
):
    first_md = tmp_path / "first.md"
    first_md.write_text("# First view\n")
    second_md = tmp_path / "second.md"
    second_md.write_text("# Second view\n")
    out = tmp_path / "view.html"
    csv = write_csv(CSV)
    spec = make_spec([("First", csv), ("Second", csv)], out)
    spec = dataclasses.replace(
        spec,
        views=(
            dataclasses.replace(spec.views[0], title_md=first_md),
            dataclasses.replace(spec.views[1], title_md=second_md),
        ),
    )
    render(spec)
    html = out.read_text()
    assert "<h1>First view</h1>" in html and "<h1>Second view</h1>" in html
    # Visibility, not display: every caption keeps its space so the page height
    # cannot change when the view does. See test_captions_do_not_change_page_flow.
    assert '<div class="caption active" data-view="first">' in html
    assert '<div class="caption" data-view="second">' in html


def test_captions_are_stacked_so_switching_cannot_move_the_page(
    tmp_path, write_csv, make_spec
):
    """The reported "structure jumps" bug, pinned in the markup that fixes it.

    Captions used to be `display: none`, so switching to a shorter one shortened
    the document -- which scrolls the page and, when it takes the scrollbar away,
    widens the content box and resizes the Mol* canvas sideways.
    """
    out = tmp_path / "view.html"
    csv = write_csv(CSV)
    md = tmp_path / "c.md"
    md.write_text("# A caption\n")
    spec = make_spec([("First", csv), ("Second", csv)], out)
    spec = dataclasses.replace(
        spec, views=tuple(dataclasses.replace(v, title_md=md) for v in spec.views)
    )
    render(spec)
    html = out.read_text()
    # Stacked in one grid cell and hidden with visibility, so a hidden caption
    # keeps its space and the page height cannot change.
    assert "display: grid" in html
    assert "visibility: hidden" in html
    assert "visibility: visible" in html
    assert "display: none" not in html.split("#header")[1].split("}")[0]
    # And the width half of the same bug.
    assert "scrollbar-gutter: stable" in html


def test_no_caption_divs_when_no_view_has_one(tmp_path, write_csv, make_spec):
    """#header:empty collapses it, so a page with no captions has no blank band."""
    out = tmp_path / "view.html"
    render(make_spec([("Only", write_csv(CSV))], out))
    html = out.read_text()
    assert 'class="caption' not in html
    # #header:empty is what collapses it, so the rule has to be there to fire.
    assert "#header:empty { display: none; }" in html


def test_viewer_height_reaches_the_page(tmp_path, write_csv, make_spec):
    out = tmp_path / "view.html"
    spec = make_spec([("Only", write_csv(CSV))], out)
    render(dataclasses.replace(spec, viewer_height="500px"))
    html = out.read_text()
    assert "height: 500px;" in html
    assert "min-height" not in html.split("#viewer {")[1].split("}")[0]


def test_viewer_height_is_never_overridden_by_a_floor(tmp_path, write_csv, make_spec):
    """A `30rem` floor used to silently win: below a 1600px-tall window every
    value under 30vh rendered at the same 480px, so shortening the viewer in the
    spec did nothing. The height is now used as written."""
    out = tmp_path / "view.html"
    spec = make_spec([("Only", write_csv(CSV))], out)
    render(dataclasses.replace(spec, viewer_height="30vh"))
    viewer_rule = out.read_text().split("#viewer {")[1].split("}")[0]
    assert "height: 30vh;" in viewer_rule
    assert "min-height" not in viewer_rule


def test_molstar_ui_hidden_starts_the_panels_closed(tmp_path, write_csv, make_spec):
    """Closed, not removed: the wrench is gated separately and still opens them."""
    out = tmp_path / "view.html"
    spec = make_spec([("Only", write_csv(CSV))], out)
    render(dataclasses.replace(spec, molstar_ui="hide"))
    assert "layoutShowControls: false" in out.read_text()
    render(dataclasses.replace(spec, molstar_ui="show"))
    assert "layoutShowControls: true" in out.read_text()


def test_opening_orientation_becomes_the_mvs_camera(rows):
    """So the page opens already framed instead of snapping after the load."""
    from prot_struct_viz import Orientation

    opening = Orientation(position=(1.0, 2.0, 3.0), target=(0.0, 0.0, 0.0)).as_dict()
    state, _ = build_state(
        [_build(rows, slug="one"), _build(rows, slug="two")],
        "mmcif",
        "structure.cif",
        opening,
    )
    cameras = [n for n in _walk(state["root"]) if n["kind"] == "camera"]
    assert len(cameras) == 1
    assert cameras[0]["params"]["position"] == [1.0, 2.0, 3.0]


def test_no_camera_node_without_an_opening_orientation(rows):
    state, _ = build_state(
        [_build(rows, slug="one"), _build(rows, slug="two")],
        "mmcif",
        "structure.cif",
    )
    assert not [n for n in _walk(state["root"]) if n["kind"] == "camera"]


def test_the_mvs_camera_is_the_first_view_s(tmp_path, write_csv, make_spec):
    """MVS holds one camera, and the page opens on the first view.

    A later view's orientation must not reach it, or the page would open framed
    on something the reader is not looking at.
    """
    from prot_struct_viz import Orientation

    out = tmp_path / "view.html"
    csv = write_csv(CSV)
    spec = make_spec([("First", csv), ("Second", csv)], out)
    spec = dataclasses.replace(
        spec,
        views=tuple(
            dataclasses.replace(
                view,
                orientation=Orientation(
                    position=(index + 1.0, 0.0, 0.0), target=(0.0, 0.0, 0.0)
                ),
            )
            for index, view in enumerate(spec.views)
        ),
    )
    render(spec)
    cameras = [
        n
        for n in _walk(_embedded_state(out.read_text())["root"])
        if n["kind"] == "camera"
    ]
    assert len(cameras) == 1
    assert cameras[0]["params"]["position"] == [1.0, 0.0, 0.0]


def test_orientations_reach_the_page_in_view_order(tmp_path, write_csv, make_spec):
    from prot_struct_viz import Orientation

    out = tmp_path / "view.html"
    csv = write_csv(CSV)
    spec = make_spec([("First", csv), ("Second", csv)], out)
    spec = dataclasses.replace(
        spec,
        views=(
            spec.views[0],
            dataclasses.replace(
                spec.views[1],
                orientation=Orientation(
                    position=(1.0, 2.0, 3.0), target=(0.0, 0.0, 0.0), radius=5.0
                ),
            ),
        ),
    )
    render(spec)
    html = out.read_text()
    embedded = json.loads(re.search(r"var ORIENTATIONS = (.*?);\n", html).group(1))
    # A view with no orientation must embed null, not be dropped: the page indexes
    # this array by the selected view.
    assert embedded[0] is None
    assert embedded[1] == {
        "position": [1.0, 2.0, 3.0],
        "target": [0.0, 0.0, 0.0],
        "up": [0.0, 1.0, 0.0],
        "radius": 5.0,
    }
    # The animated setter, not the raw one -- see the template comment. The
    # duration is an argument because a deep link and Reset both want it at 0.
    assert "managers.camera.setSnapshot(" in html


def test_camera_capture_is_hidden_behind_the_url_fragment(
    tmp_path, write_csv, make_spec
):
    """An authoring tool must not be furniture on a published page."""
    out = tmp_path / "view.html"
    render(make_spec([("Only", write_csv(CSV))], out))
    html = out.read_text()
    assert '<button id="copy-camera" type="button" hidden' in html
    # Read through the fragment parser, so that #view=<slug>&camera keeps working.
    assert "if (fragment().camera) {" in html
    assert "window.location.hash === '#camera'" not in html
    assert "window.psvCamera" in html


def test_deep_link_fragment_selects_a_view(tmp_path, write_csv, make_spec):
    """`#view=<slug>` has to act at runtime, not change what is served."""
    out = tmp_path / "view.html"
    csv = write_csv(CSV)
    render(make_spec([("First", csv), ("Second", csv)], out))
    html = out.read_text()
    assert "token.indexOf('view=') === 0" in html
    assert "function selectFromFragment()" in html
    assert "addEventListener('hashchange'" in html
    # An unknown slug is not an error; it leaves the first view selected.
    assert "VIEWS.indexOf(wanted) === -1) return false" in html
    # ...and it has to run on load, not only when the fragment is edited later.
    on_load = html.split("return load().then(")[1].split("});")[0]
    assert "selectFromFragment()" in on_load
    # A view pinning no camera of its own inherits the opening view's, so a link
    # to it lands where switching to it by hand would.
    assert "ORIENTATIONS[activeIndex()] || ORIENTATIONS[0]" in html
    # The served markup is untouched -- no <option> is marked selected -- so a
    # reader with no fragment still gets the first view, and the deep link is
    # purely a runtime override.
    assert "selected" not in re.search(r"<select.*?</select>", html, re.S).group(0)


def test_load_always_places_the_camera(tmp_path, write_csv, make_spec):
    """The MVS camera node is only an approximation.

    MolViewSpec reads its `position` as a reference camera and scales the distance
    to the target by 1/(2*sin(fov/2)), about 1.31 at the default field of view, so
    the node alone opens a third too far out and every capture-and-paste of a
    camera drifts further. The page has to re-place the camera itself, on every
    load and not only when a fragment picked the view.
    """
    out = tmp_path / "view.html"
    csv = write_csv(CSV)
    render(make_spec([("First", csv), ("Second", csv)], out))
    on_load = out.read_text().split("return load().then(")[1].split("});")[0]
    # After selectFromFragment, so it places the camera of whichever view the
    # fragment chose rather than of the first one.
    assert on_load.index("selectFromFragment()") < on_load.index(
        "placeOpeningCamera();"
    )


def test_switching_views_rewrites_the_fragment(tmp_path, write_csv, make_spec):
    """Sharing a view should be copying the address bar."""
    out = tmp_path / "view.html"
    csv = write_csv(CSV)
    render(make_spec([("First", csv), ("Second", csv)], out))
    html = out.read_text()
    assert "history.replaceState(" in html
    assert "history.pushState(" not in html  # Back leaves the page, as it always did
    assert "if (fragment().camera) tokens.push('camera');" in html


def test_reset_restores_the_camera_of_the_view_you_are_on(
    tmp_path, write_csv, make_spec
):
    """Reloading the state resets the camera to the first view's pose; undo that."""
    out = tmp_path / "view.html"
    csv = write_csv(CSV)
    render(make_spec([("First", csv), ("Second", csv)], out))
    html = out.read_text()
    reset = html.split("document.getElementById('reset-view')")[1]
    assert "placeOpeningCamera()" in reset.split("})")[0]


def test_snapshot_stepper_is_hidden(tmp_path, write_csv, make_spec):
    """Mol*'s "[1/1] <timestamp>" widget. Nothing here ever uses MVS snapshots."""
    out = tmp_path / "view.html"
    render(make_spec([("Only", write_csv(CSV))], out))
    html = out.read_text()
    assert ".msp-state-snapshot-viewport-controls { display: none; }" in html


def test_rendered_html_embeds_a_loadable_archive(tmp_path, write_csv, make_spec):
    out = tmp_path / "view.html"
    render(make_spec([("Main", write_csv(CSV))], out))
    payload = re.search(
        r'<script id="mvsx-payload" type="text/plain">(.*?)</script>',
        out.read_text(),
        re.S,
    ).group(1)
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(payload.strip()))) as zf:
        assert STATE_MEMBER in zf.namelist()


def test_render_renders_the_markdown_title(tmp_path, write_csv, make_spec):
    title = tmp_path / "title.md"
    title.write_text("# Neuraminidase\n\nSites of **interest**.\n")
    out = tmp_path / "view.html"
    render(_with_title(make_spec([("Main", write_csv(CSV))], out), title))
    html = out.read_text()
    assert "<h1>Neuraminidase</h1>" in html
    assert "<strong>interest</strong>" in html


def test_render_requires_html_suffix(tmp_path, write_csv, make_spec):
    with pytest.raises(InputError, match="must end in '.html'"):
        render(make_spec([("Main", write_csv(CSV))], tmp_path / "view.htm"))


def test_render_fatal_mode_still_writes_the_report(tmp_path, write_csv, make_spec):
    out = tmp_path / "view.html"
    with pytest.raises(InputError, match="does not match the structure"):
        render(make_spec([("Main", write_csv(CSV))], out, on_mismatch="error-any"))
    assert not out.exists()
    assert (tmp_path / "view_report.txt").is_file()


def test_a_later_view_can_be_the_fatal_one(tmp_path, write_csv, make_spec):
    """Every view is validated, not just the first one the loop reaches."""
    out = tmp_path / "view.html"
    fine = write_csv(CSV, name="fine.csv")
    # A residue the structure does not have, which is what error-extra-in-csv is
    # about. The first view is clean, so only the second can trip it.
    broken = write_csv(CSV + "A,99999,#000000,ghost,,\n", name="broken.csv")
    with pytest.raises(InputError, match="does not match the structure"):
        render(
            make_spec(
                [("Fine", fine), ("Broken", broken)],
                out,
                on_mismatch="error-extra-in-csv",
            )
        )
    assert not out.exists()
    # Both views were reported on before the run was failed, so the report says
    # which one was at fault rather than stopping at the first.
    assert (tmp_path / "view_report.txt").read_text().count("=== view:") == 2


def test_state_validates_against_the_mvs_schema(rows):
    """Catch a malformed state here rather than as a blank viewer in a browser.

    This is the Python-side counterpart to `mvs-validate`; see CLAUDE.md for the
    Mol*-side check.
    """
    from molviewspec import validate_state_tree

    for config in (ViewConfig(), ViewConfig(assembly="1", waters="show")):
        validate_state_tree(json.dumps(_state(rows, config)))

    # And the multi-view shape, which is a different tree: two structure nodes
    # off one parse, each carrying a ref.
    state, _ = build_state(
        [_build(rows, slug="one"), _build(rows, slug="two")],
        "mmcif",
        "structure.cif",
    )
    validate_state_tree(json.dumps(state))


def test_every_annotation_row_names_a_representation_or_layer(rows):
    """A row with colour but no component would colour nothing that is drawn."""
    for row in rows:
        assert {"base_rep", "extra_rep", "het_layer"} & set(row), row


def test_per_chain_override_does_not_reach_csv_named_heteroatoms(coloring, deposited):
    """A chain's polymer representation would draw nothing for its ligand."""
    rows = build_annotations(coloring, deposited, ViewConfig(), {"A": "cartoon"})
    assert _row(rows, "A", 0)["base_rep"] == "ball_and_stick"
    assert _row(rows, "A", 998)["base_rep"] == "ball_and_stick"
    # The polymer on that chain still follows the override.
    assert _row(rows, "A", 100)["base_rep"] == "cartoon"


# --- persistent 3D labels -------------------------------------------------------


@pytest.fixture
def label_args(coloring, deposited, structure):
    """The `labels` tuple build_state takes, for the asymmetric unit."""
    return (coloring, deposited, residue_centroids(structure), [])


@pytest.fixture
def assembly_label_args(coloring, deposited, structure):
    return (
        coloring,
        deposited,
        residue_centroids(structure),
        assembly_instance_transforms(structure, "1"),
    )


def _residue_atoms(structure, chain_name, seq_id, ins_code=""):
    for chain in structure[0]:
        if chain.name != chain_name:
            continue
        for residue in chain:
            if residue.seqid.num == seq_id and residue.seqid.icode.strip() == ins_code:
                return [(a.pos.x, a.pos.y, a.pos.z) for a in residue]
    raise AssertionError(f"no residue {chain_name}/{seq_id}{ins_code}")


def test_only_show_label_rows_get_a_label(rows, label_args):
    labels = _labels(_state(rows, labels=label_args))
    # Only 412A sets show_label; the other five rows are tooltip-only.
    assert set(labels) == {"site 412A"}


def test_labels_are_placed_on_their_own_residues(rows, label_args, structure):
    """The regression test for labels piling up at the centre of the structure.

    Mol*'s label_from_uri derives one position from the boundary sphere of every
    atom a row matches, across every symmetry copy, which put every label in the
    middle of the assembly. Each label must sit inside the residue it names.
    """
    labels = _labels(_state(rows, labels=label_args))
    position = labels["site 412A"]["position"]
    atoms = _residue_atoms(structure, "A", 412, "A")
    closest = min(
        sum((a - b) ** 2 for a, b in zip(position, atom)) ** 0.5 for atom in atoms
    )
    assert closest < 5.0, f"label is {closest:.1f} A from its residue"

    # And emphatically not at the centre of everything.
    all_atoms = [
        (a.pos.x, a.pos.y, a.pos.z) for c in structure[0] for r in c for a in r
    ]
    centre = [sum(c[i] for c in all_atoms) / len(all_atoms) for i in range(3)]
    to_centre = sum((p - c) ** 2 for p, c in zip(position, centre)) ** 0.5
    assert to_centre > 5.0


def test_label_color_and_size_default(rows, label_args):
    from prot_struct_viz._config import DEFAULT_LABEL_COLOR, DEFAULT_LABEL_SIZE

    params = _labels(_state(rows, labels=label_args))["site 412A"]
    assert params["label_color"] == DEFAULT_LABEL_COLOR
    assert params["label_size"] == DEFAULT_LABEL_SIZE


def test_label_color_and_size_from_the_csv(write_csv, deposited, structure):
    coloring = parse_csv(
        write_csv(
            "chain,residue,color,label,show_label,label_color,label_size\n"
            "A,118,red,Arg118,True,navy,4.5\n"
        )
    )
    rows = build_annotations(coloring, deposited, ViewConfig(), {})
    args = (coloring, deposited, residue_centroids(structure), [])
    params = _labels(_state(rows, labels=args))["Arg118"]
    assert params["label_color"] == "#000080"
    assert params["label_size"] == 4.5


def test_assembly_replicates_labels_onto_every_symmetry_copy(
    rows, assembly_label_args, structure
):
    state = _state(rows, ViewConfig(assembly="1"), labels=assembly_label_args)
    groups = _primitive_groups(state)
    assert len(groups) == 1
    matrices = groups[0]["params"]["instances"]
    # 1F8B's assembly 1 is a tetramer built from four operators.
    assert len(matrices) == len(assembly_instance_transforms(structure, "1")[0][1]) == 4
    assert all(len(m) == 16 for m in matrices)
    # The first is the identity, in column-major order.
    assert matrices[0] == [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def test_asymmetric_unit_needs_no_instances(rows, label_args):
    groups = _primitive_groups(_state(rows, labels=label_args))
    assert len(groups) == 1
    assert groups[0]["params"].get("instances") is None


def test_no_primitives_group_without_labels(write_csv, deposited, structure):
    coloring = parse_csv(write_csv("chain,residue,color\nA,100,red\n"))
    rows = build_annotations(coloring, deposited, ViewConfig(), {})
    args = (coloring, deposited, residue_centroids(structure), [])
    assert _primitive_groups(_state(rows, labels=args)) == []


def test_label_on_an_undisplayed_chain_is_reported(write_csv, structure):
    from prot_struct_viz.structure import get_deposited_residues

    coloring = parse_csv(
        write_csv("chain,residue,color,label,show_label\nA,118,red,Arg118,True\n")
    )
    subset = get_deposited_residues(structure, ["B"])
    rows = build_annotations(coloring, subset, ViewConfig(), {})
    _, unplaced = build_state(
        [
            _build(
                rows,
                ViewConfig(chains=("B",)),
                labels=(coloring, subset, residue_centroids(structure, ["B"]), []),
            )
        ],
        "mmcif",
        "structure.cif",
    )
    assert unplaced == {SLUG: [("A", "118")]}


def test_labelled_state_validates(rows, assembly_label_args):
    from molviewspec import validate_state_tree

    state = _state(rows, ViewConfig(assembly="1"), labels=assembly_label_args)
    validate_state_tree(json.dumps(state))
