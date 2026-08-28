"""Tests for the YAML spec loader.

The format's whole claim is that a spec says what it means: no defaults are
filled in behind the author's back, and anything it gets wrong is named.
"""

import pytest

from prot_struct_viz import load_spec
from prot_struct_viz._config import InputError

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


@pytest.mark.parametrize("key", ["structure", "out", "assembly", "on_mismatch"])
def test_missing_shared_key_is_fatal(tmp_path, key):
    body = "\n".join(
        line for line in _minimal().splitlines() if not line.startswith(f"{key}:")
    )
    with pytest.raises(InputError, match=f"missing top-level .*{key}"):
        load_spec(_spec(tmp_path, body))


@pytest.mark.parametrize(
    "key",
    ["default_color", "default_representation", "waters", "ligands", "glycans", "ions"],
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
