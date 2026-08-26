"""Tests for the annotation table, the MVS state, and the HTML output."""

import base64
import json
import re
import zipfile

import pytest

from prot_struct_viz import ViewConfig, render
from prot_struct_viz._config import InputError
from prot_struct_viz.residues import parse_csv
from prot_struct_viz.structure import assembly_instance_transforms, residue_centroids
from prot_struct_viz.viewer import (
    ANNOTATION_MEMBER,
    MOLSTAR_VERSION,
    STATE_MEMBER,
    build_annotations,
    build_mvsx,
    build_state,
)


def _state(rows, config=None, scheme="Default", labels=None):
    """build_state's state, dropping the unplaced-label list the callers ignore."""
    state, _ = build_state(
        rows, "mmcif", "structure.cif", config or ViewConfig(), scheme, labels=labels
    )
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
    assert _row(rows, "A", 412)["color:Default"] == "#2ca02c"
    assert _row(rows, "A", 412, "A")["color:Default"] == "#d62728"
    assert _row(rows, "A", 412, "B")["color:Default"] == "#ff7f0e"


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
    assert "color:Default" not in _row(rows, "A", 999)


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
    assert _row(rows, "A", 100)["color:Default"] == "#0000ff"


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
    archive = build_mvsx(state, coordinate_text, "structure.cif", rows)
    with zipfile.ZipFile(__import__("io").BytesIO(archive)) as zf:
        assert set(zf.namelist()) == {STATE_MEMBER, "structure.cif", ANNOTATION_MEMBER}
        assert json.loads(zf.read(ANNOTATION_MEMBER)) == rows
        assert zf.read("structure.cif").decode() == coordinate_text


def test_render_writes_html_and_report(tmp_path, write_csv, fixture_cif):
    out = tmp_path / "view.html"
    render(str(fixture_cif), write_csv(CSV), out, title_md=None)
    assert out.is_file()
    assert (tmp_path / "view_report.txt").is_file()

    html = out.read_text()
    assert f"molstar@{MOLSTAR_VERSION}/build/viewer/molstar.js" in html
    assert "loadMvsData('base64,' + payload, 'mvsx')" in html
    # Mol*'s own UI stays enabled so the view can be re-styled interactively.
    assert "layoutShowControls: true" in html


def test_rendered_html_embeds_a_loadable_archive(tmp_path, write_csv, fixture_cif):
    out = tmp_path / "view.html"
    render(str(fixture_cif), write_csv(CSV), out)
    payload = re.search(
        r'<script id="mvsx-payload" type="text/plain">(.*?)</script>',
        out.read_text(),
        re.S,
    ).group(1)
    with zipfile.ZipFile(
        __import__("io").BytesIO(base64.b64decode(payload.strip()))
    ) as zf:
        assert STATE_MEMBER in zf.namelist()


def test_render_renders_the_markdown_title(tmp_path, write_csv, fixture_cif):
    title = tmp_path / "title.md"
    title.write_text("# Neuraminidase\n\nSites of **interest**.\n")
    out = tmp_path / "view.html"
    render(str(fixture_cif), write_csv(CSV), out, title_md=title)
    html = out.read_text()
    assert "<h1>Neuraminidase</h1>" in html
    assert "<strong>interest</strong>" in html


def test_render_requires_html_suffix(tmp_path, write_csv, fixture_cif):
    with pytest.raises(InputError, match="must end in '.html'"):
        render(str(fixture_cif), write_csv(CSV), tmp_path / "view.htm")


def test_render_fatal_mode_still_writes_the_report(tmp_path, write_csv, fixture_cif):
    out = tmp_path / "view.html"
    with pytest.raises(InputError, match="does not match the structure"):
        render(
            str(fixture_cif),
            write_csv(CSV),
            out,
            config=ViewConfig(on_mismatch="error-any"),
        )
    assert not out.exists()
    assert (tmp_path / "view_report.txt").is_file()


def test_state_validates_against_the_mvs_schema(rows):
    """Catch a malformed state here rather than as a blank viewer in a browser.

    This is the Python-side counterpart to `mvs-validate`; see CLAUDE.md for the
    Mol*-side check.
    """
    from molviewspec import validate_state_tree

    for config in (ViewConfig(), ViewConfig(assembly="1", waters="show")):
        validate_state_tree(json.dumps(_state(rows, config)))


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
        rows,
        "mmcif",
        "structure.cif",
        ViewConfig(chains=("B",)),
        "Default",
        labels=(coloring, subset, residue_centroids(structure, ["B"]), []),
    )
    assert unplaced == [("A", "118")]


def test_labelled_state_validates(rows, assembly_label_args):
    from molviewspec import validate_state_tree

    state = _state(rows, ViewConfig(assembly="1"), labels=assembly_label_args)
    validate_state_tree(json.dumps(state))
