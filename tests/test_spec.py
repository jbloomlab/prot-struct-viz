"""Tests for the YAML spec loader.

The format's whole claim is that a spec says what it means: no defaults are
filled in behind the author's back, and anything it gets wrong is named.
"""

import pytest

from prot_struct_viz import load_spec
from prot_struct_viz._config import InputError
from prot_struct_viz.spec import REQUIRED_VIEW_KEYS, SHARED_KEYS

BASE = """definitions:
  base: &base
    default_color: "#d9d9d9"
    default_representation: cartoon
    waters: hide
    ligands: show
    glycans: snfg
    ions: show
"""

ONE_VIEW = """views:
  - <<: *base
    name: Only view
    csv: coloring.csv
"""


def _minimal(views=ONE_VIEW):
    """A valid spec, as text, so a test can break exactly one thing about it."""
    return (
        "structure: 1F8B\n"
        "out: view.html\n"
        "assembly: au\n"
        "on_mismatch: report\n"
        "\n" + BASE + "\n" + views
    )


def _spec(tmp_path, body, name="spec.yaml"):
    path = tmp_path / name
    path.write_text(body)
    return path


def test_minimal_spec(tmp_path):
    spec = load_spec(_spec(tmp_path, _minimal()))
    assert spec.structure == "1F8B"
    assert spec.assembly == "au"
    assert spec.on_mismatch == "report"
    assert len(spec.views) == 1
    view = spec.views[0]
    assert view.name == "Only view"
    assert view.slug == "only-view"
    assert view.config.default_representation == "cartoon"
    # Omitted optional keys mean "none", which is the only default there is.
    assert view.config.chains is None
    assert view.title_md is None
    assert view.chain_representation is None


def test_paths_resolve_relative_to_the_spec(tmp_path):
    """A spec names files beside it, so it works from any working directory."""
    nested = tmp_path / "example"
    nested.mkdir()
    spec = load_spec(_spec(nested, _minimal()))
    assert spec.views[0].csv == nested / "coloring.csv"
    assert spec.out == nested / "view.html"


def test_absolute_paths_are_left_alone(tmp_path):
    spec = load_spec(
        _spec(tmp_path, _minimal().replace("csv: coloring.csv", "csv: /tmp/c.csv"))
    )
    assert str(spec.views[0].csv) == "/tmp/c.csv"


def test_anchors_share_keys_and_the_view_still_wins(tmp_path):
    spec = load_spec(
        _spec(
            tmp_path,
            _minimal("""views:
  - <<: *base
    name: One
    csv: a.csv
  - <<: *base
    name: Two
    csv: b.csv
    glycans: hide
    default_representation: surface
"""),
        )
    )
    assert [v.name for v in spec.views] == ["One", "Two"]
    assert spec.views[0].config.glycans == "snfg"
    assert spec.views[1].config.glycans == "hide"
    assert spec.views[1].config.default_representation == "surface"


def test_shared_keys_are_stamped_onto_every_view(tmp_path):
    """A view's config is the whole truth about how that view is built."""
    body = _minimal().replace("assembly: au", "assembly: '1'")
    spec = load_spec(_spec(tmp_path, body))
    assert spec.views[0].config.assembly == "1"
    assert spec.views[0].config.on_mismatch == "report"


@pytest.mark.parametrize("key", SHARED_KEYS)
def test_missing_shared_key_is_fatal(tmp_path, key):
    body = "\n".join(
        line for line in _minimal().splitlines() if not line.startswith(f"{key}:")
    )
    with pytest.raises(InputError, match=f"missing top-level .*{key}"):
        load_spec(_spec(tmp_path, body))


@pytest.mark.parametrize(
    "key", [k for k in REQUIRED_VIEW_KEYS if k not in ("name", "csv")]
)
def test_missing_view_key_is_fatal(tmp_path, key):
    """No defaults: a view states its options or the spec is rejected."""
    body = "\n".join(
        line
        for line in _minimal().splitlines()
        if not line.strip().startswith(f"{key}:")
    )
    with pytest.raises(InputError, match=f"views\\[0\\] is missing .*{key}"):
        load_spec(_spec(tmp_path, body))


def test_unknown_top_level_key_is_fatal(tmp_path):
    with pytest.raises(InputError, match="unknown top-level key \\['colour'\\]"):
        load_spec(_spec(tmp_path, _minimal() + "colour: blue\n"))


def test_unknown_view_key_is_fatal(tmp_path):
    """A typo would otherwise be silently ignored, which is the worst outcome."""
    body = _minimal().replace(
        "csv: coloring.csv", "csv: coloring.csv\n    glycan: hide"
    )
    with pytest.raises(InputError, match=r"unknown key in views\[0\] \['glycan'\]"):
        load_spec(_spec(tmp_path, body))


def test_definitions_is_ignored_not_rendered(tmp_path):
    """It exists to hold anchors; it must not become a view or a default."""
    spec = load_spec(_spec(tmp_path, _minimal()))
    assert len(spec.views) == 1


def test_bad_option_value_is_fatal(tmp_path):
    body = _minimal().replace(
        "default_representation: cartoon", "default_representation: sausage"
    )
    with pytest.raises(InputError, match="default_representation must be one of"):
        load_spec(_spec(tmp_path, body))


@pytest.mark.parametrize("key", ["waters", "ligands", "glycans", "ions"])
def test_bad_heteroatom_flag_is_fatal(tmp_path, key):
    """A typo here would silently change what the figure shows."""
    body = "\n".join(
        f"    {key}: sometimes" if line.strip().startswith(f"{key}:") else line
        for line in _minimal().splitlines()
    )
    with pytest.raises(InputError, match=f"{key} must be one of"):
        load_spec(_spec(tmp_path, body))


def test_bad_default_color_is_fatal(tmp_path):
    """An unrecognized color reaches Mol* as a string it silently ignores."""
    body = _minimal().replace('default_color: "#d9d9d9"', "default_color: not-a-color")
    with pytest.raises(InputError, match="default_color: .*is not a valid color"):
        load_spec(_spec(tmp_path, body))


def test_default_color_is_normalized(tmp_path):
    """A CSS name and a short hex reach the state the same way a CSV cell does."""
    body = _minimal().replace('default_color: "#d9d9d9"', "default_color: red")
    assert load_spec(_spec(tmp_path, body)).views[0].config.default_color == "#ff0000"
    body = _minimal().replace('default_color: "#d9d9d9"', 'default_color: "#ABC"')
    assert load_spec(_spec(tmp_path, body)).views[0].config.default_color == "#aabbcc"


def test_bad_on_mismatch_is_fatal(tmp_path):
    body = _minimal().replace("on_mismatch: report", "on_mismatch: shout")
    with pytest.raises(InputError, match="on_mismatch must be one of"):
        load_spec(_spec(tmp_path, body))


def test_empty_views_is_fatal(tmp_path):
    body = _minimal("views: []\n")
    with pytest.raises(InputError, match="views must be a non-empty list"):
        load_spec(_spec(tmp_path, body))


def test_duplicate_view_names_are_fatal(tmp_path):
    body = _minimal("""views:
  - <<: *base
    name: Same
    csv: a.csv
  - <<: *base
    name: Same
    csv: b.csv
""")
    with pytest.raises(InputError, match="two views share the name 'Same'"):
        load_spec(_spec(tmp_path, body))


def test_names_that_collide_once_simplified_are_fatal(tmp_path):
    """Slugs name archive members and MVS refs, so they must stay distinct."""
    body = _minimal("""views:
  - <<: *base
    name: Antigenic sites
    csv: a.csv
  - <<: *base
    name: "Antigenic  Sites"
    csv: b.csv
""")
    with pytest.raises(InputError, match="share the name \\(once simplified\\)"):
        load_spec(_spec(tmp_path, body))


def test_name_with_no_usable_characters_is_fatal(tmp_path):
    body = _minimal().replace("name: Only view", 'name: "***"')
    with pytest.raises(InputError, match="has no alphanumeric characters"):
        load_spec(_spec(tmp_path, body))


def test_chains_accepts_a_list_or_a_string(tmp_path):
    listed = _minimal().replace("csv: coloring.csv", "csv: c.csv\n    chains: [A, B]")
    assert load_spec(_spec(tmp_path, listed)).views[0].config.chains == ("A", "B")
    joined = _minimal().replace("csv: coloring.csv", "csv: c.csv\n    chains: 'A, B'")
    assert load_spec(_spec(tmp_path, joined)).views[0].config.chains == ("A", "B")


def test_empty_chains_is_fatal(tmp_path):
    body = _minimal().replace("csv: coloring.csv", "csv: c.csv\n    chains: []")
    with pytest.raises(InputError, match="omit the key to show every chain"):
        load_spec(_spec(tmp_path, body))


def test_not_yaml_is_fatal(tmp_path):
    with pytest.raises(InputError, match="not valid YAML"):
        load_spec(_spec(tmp_path, "views: [\n"))


def test_empty_file_is_fatal(tmp_path):
    with pytest.raises(InputError, match="is empty"):
        load_spec(_spec(tmp_path, ""))


def test_missing_file_is_fatal(tmp_path):
    with pytest.raises(InputError, match="no such file"):
        load_spec(tmp_path / "absent.yaml")


# --- page-level presentation keys ------------------------------------------------


def test_page_keys_default_to_todays_behaviour(tmp_path):
    """These have defaults, unlike per-view keys, so old specs keep working."""
    spec = load_spec(_spec(tmp_path, _minimal()))
    assert spec.viewer_height == "70vh"
    assert spec.molstar_ui == "show"


def test_page_keys_can_be_set(tmp_path):
    body = _minimal().replace(
        "on_mismatch: report\n",
        "on_mismatch: report\nviewer_height: 800px\nmolstar_ui: hide\n",
    )
    spec = load_spec(_spec(tmp_path, body))
    assert spec.viewer_height == "800px"
    assert spec.molstar_ui == "hide"


@pytest.mark.parametrize("value", ["800", "big", "800 px", "-3rem", "80vhh"])
def test_bad_viewer_height_is_fatal(tmp_path, value):
    """A bad length would silently collapse the viewport in the browser."""
    body = _minimal().replace(
        "on_mismatch: report\n", f"on_mismatch: report\nviewer_height: '{value}'\n"
    )
    with pytest.raises(InputError, match="is not a CSS length"):
        load_spec(_spec(tmp_path, body))


def test_bad_molstar_ui_is_fatal(tmp_path):
    body = _minimal().replace(
        "on_mismatch: report\n", "on_mismatch: report\nmolstar_ui: maybe\n"
    )
    with pytest.raises(InputError, match="molstar_ui must be one of"):
        load_spec(_spec(tmp_path, body))


# --- per-view orientation --------------------------------------------------------


ORIENTED = """views:
  - <<: *base
    name: Only view
    csv: coloring.csv
    orientation:
      position: [11.2, -48.6, 187.3]
      target: [-0.4, -57.4, 13.8]
      up: [0.1, 0.06, -0.99]
      radius: 76.1
"""


def test_orientation_is_parsed(tmp_path):
    view = load_spec(_spec(tmp_path, _minimal(ORIENTED))).views[0]
    assert view.orientation.position == (11.2, -48.6, 187.3)
    assert view.orientation.target == (-0.4, -57.4, 13.8)
    # Not the fallback, so the parsing branch is actually exercised.
    assert view.orientation.up == (0.1, 0.06, -0.99)
    assert view.orientation.radius == 76.1
    assert view.orientation.as_dict()["radius"] == 76.1


def test_orientation_is_optional(tmp_path):
    """Omitting it means "leave the camera alone", which is the default behaviour."""
    assert load_spec(_spec(tmp_path, _minimal())).views[0].orientation is None


def test_orientation_up_and_radius_have_fallbacks(tmp_path):
    """position and target define the view; the other two are conveniences."""
    body = _minimal("""views:
  - <<: *base
    name: Only view
    csv: coloring.csv
    orientation:
      position: [1, 2, 3]
      target: [0, 0, 0]
""")
    orientation = load_spec(_spec(tmp_path, body)).views[0].orientation
    assert orientation.up == (0.0, 1.0, 0.0)
    assert orientation.radius is None
    # radius is left out entirely rather than sent as null, so Mol* fits the scene.
    assert "radius" not in orientation.as_dict()


def test_orientation_vector_must_be_three_numbers(tmp_path):
    """YAML's booleans are ints, so `true` would otherwise pass as 1."""
    for value, message in [
        ("[1, 2]", "list of 3 numbers"),
        ("[1, 2, true]", "must be 3 numbers"),
        ('[1, 2, "x"]', "must be 3 numbers"),
    ]:
        body = _minimal(f"""views:
  - <<: *base
    name: Only view
    csv: coloring.csv
    orientation:
      position: {value}
      target: [0, 0, 0]
""")
        with pytest.raises(InputError, match=message):
            load_spec(_spec(tmp_path, body))


def test_orientation_radius_must_be_a_number(tmp_path):
    body = _minimal("""views:
  - <<: *base
    name: Only view
    csv: coloring.csv
    orientation:
      position: [1, 2, 3]
      target: [0, 0, 0]
      radius: far
""")
    with pytest.raises(InputError, match="orientation radius must be a number"):
        load_spec(_spec(tmp_path, body))


@pytest.mark.parametrize("key", ["position", "target"])
def test_orientation_needs_position_and_target(tmp_path, key):
    body = "\n".join(
        line
        for line in _minimal(ORIENTED).splitlines()
        if not line.strip().startswith(f"{key}:")
    )
    with pytest.raises(InputError, match="orientation is missing"):
        load_spec(_spec(tmp_path, body))


def test_orientation_rejects_a_short_vector(tmp_path):
    body = _minimal(ORIENTED).replace(
        "position: [11.2, -48.6, 187.3]", "position: [1, 2]"
    )
    with pytest.raises(InputError, match="must be a list of 3 numbers"):
        load_spec(_spec(tmp_path, body))


def test_orientation_rejects_a_non_number(tmp_path):
    body = _minimal(ORIENTED).replace(
        "position: [11.2, -48.6, 187.3]", "position: [1, 2, x]"
    )
    with pytest.raises(InputError, match="must be 3 numbers"):
        load_spec(_spec(tmp_path, body))


def test_orientation_rejects_unknown_keys(tmp_path):
    """A stray key here is a typo that would otherwise be silently ignored."""
    body = _minimal(ORIENTED).replace("      radius: 76.1", "      zoom: 76.1")
    with pytest.raises(InputError, match=r"unknown key in views\[0\] orientation"):
        load_spec(_spec(tmp_path, body))
