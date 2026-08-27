"""Tests for CSV parsing: the schema, the fail-fast rules, and normalization."""

import pathlib

import pytest

from prot_struct_viz._config import InputError
from prot_struct_viz.residues import (
    normalize_color,
    parse_chain_representations,
    parse_csv,
    split_residue,
)

GOOD = """chain,residue,color,label,show_label,representation
A,169A,red,Insertion-coded site,True,ball-and-stick
A,150,#1f77b4,hover only,,
A,412B,darkgray,,,spacefill
B,1,#ff0000,a glycan the CSV claims,,
"""


def test_parse_good_csv(write_csv):
    coloring = parse_csv(write_csv(GOOD))
    assert coloring.scheme_names == ["Default"]
    specs = {spec.key: spec for spec in coloring.specs}
    assert set(specs) == {("A", "169A"), ("A", "150"), ("A", "412B"), ("B", "1")}

    inserted = specs[("A", "169A")]
    assert inserted.colors == {"Default": "#ff0000"}
    assert inserted.label == "Insertion-coded site"
    assert inserted.show_label is True
    assert inserted.representation == "ball-and-stick"

    # A tooltip without a persistent label, and a persistent label are separable.
    assert specs[("A", "150")].show_label is False
    assert specs[("A", "150")].label == "hover only"
    assert specs[("A", "412B")].label is None


def test_residue_stays_a_string(write_csv):
    """A residue number must never be coerced to an int, or 0169 == 169."""
    coloring = parse_csv(write_csv("chain,residue,color\nA,0169,red\n"))
    assert coloring.specs[0].residue == "0169"


@pytest.mark.parametrize(
    "value,expected",
    [
        ("#1f77b4", "#1f77b4"),
        ("#1F77B4", "#1f77b4"),
        ("#abc", "#aabbcc"),
        ("red", "#ff0000"),
        ("RED", "#ff0000"),
        (" darkgray ", "#a9a9a9"),
    ],
)
def test_normalize_color(value, expected):
    assert normalize_color(value) == expected


@pytest.mark.parametrize("value", ["", "notacolor", "#12345", "0x00ff00", "rgb(1,2,3)"])
def test_normalize_color_rejects(value):
    with pytest.raises(InputError, match="not a valid color"):
        normalize_color(value)


@pytest.mark.parametrize(
    "value,expected", [("52", (52, "")), ("52A", (52, "A")), ("-5", (-5, ""))]
)
def test_split_residue(value, expected):
    assert split_residue(value) == expected


@pytest.mark.parametrize("value", ["", "52AB", "5 2", "A52", "52.0"])
def test_split_residue_rejects(value):
    with pytest.raises(InputError):
        split_residue(value)


def test_missing_required_column(write_csv):
    with pytest.raises(InputError, match="missing required column"):
        parse_csv(write_csv("chain,color\nA,red\n"))


def test_missing_color_column(write_csv):
    with pytest.raises(InputError, match="missing required column 'color'"):
        parse_csv(write_csv("chain,residue,label\nA,5,hi\n"))


def test_blank_required_cell_is_fatal(write_csv):
    with pytest.raises(
        InputError, match="line 3, column 'color': required value is blank"
    ):
        parse_csv(write_csv("chain,residue,color\nA,5,red\nA,6,\n"))


def test_blank_chain_is_fatal(write_csv):
    with pytest.raises(InputError, match="line 2, column 'chain'"):
        parse_csv(write_csv("chain,residue,color\n,5,red\n"))


def test_all_problems_reported_together(write_csv):
    text = "chain,residue,color\nA,5,notacolor\nA,6X7,red\n"
    with pytest.raises(InputError) as excinfo:
        parse_csv(write_csv(text))
    message = str(excinfo.value)
    assert "line 2" in message and "line 3" in message


def test_show_label_without_label_is_fatal(write_csv):
    text = "chain,residue,color,show_label\nA,5,red,True\n"
    with pytest.raises(InputError, match="show_label is True but 'label' is empty"):
        parse_csv(write_csv(text))


def test_bad_show_label_is_fatal(write_csv):
    text = "chain,residue,color,label,show_label\nA,5,red,hi,maybe\n"
    with pytest.raises(InputError, match="not a boolean"):
        parse_csv(write_csv(text))


def test_show_label_defaults_false(write_csv):
    coloring = parse_csv(write_csv("chain,residue,color\nA,5,red\n"))
    assert coloring.specs[0].show_label is False


def test_unknown_representation_is_fatal(write_csv):
    text = "chain,residue,color,representation\nA,5,red,cartoonish\n"
    with pytest.raises(InputError, match="representation"):
        parse_csv(write_csv(text))


def test_duplicate_key_is_fatal(write_csv):
    text = "chain,residue,color\nA,5,red\nA,5,blue\n"
    with pytest.raises(InputError, match="duplicate entry"):
        parse_csv(write_csv(text))


def test_duplicate_column_is_fatal(write_csv):
    text = "chain,residue,color,color\nA,5,red,blue\n"
    with pytest.raises(InputError, match="duplicate column name"):
        parse_csv(write_csv(text))


def test_no_data_rows_is_fatal(write_csv):
    with pytest.raises(InputError, match="no data rows"):
        parse_csv(write_csv("chain,residue,color\n"))


def test_multiple_schemes(write_csv):
    text = "chain,residue,color:Entropy,color:Escape\nA,5,red,#000000\n"
    coloring = parse_csv(write_csv(text))
    assert coloring.scheme_names == ["Entropy", "Escape"]
    assert coloring.specs[0].colors == {"Entropy": "#ff0000", "Escape": "#000000"}


def test_mixing_bare_and_named_color_columns_is_fatal(write_csv):
    text = "chain,residue,color,color:Escape\nA,5,red,blue\n"
    with pytest.raises(InputError, match="both a bare 'color' column"):
        parse_csv(write_csv(text))


def test_empty_scheme_name_is_fatal(write_csv):
    with pytest.raises(InputError, match="empty scheme name"):
        parse_csv(write_csv("chain,residue,color:\nA,5,red\n"))


def test_missing_file(tmp_path):
    with pytest.raises(InputError, match="no such file"):
        parse_csv(tmp_path / "absent.csv")


def test_chain_representations(write_csv):
    path = write_csv("chain,representation\nA,cartoon\nB,surface\n", "chains.csv")
    assert parse_chain_representations(path) == {"A": "cartoon", "B": "surface"}


def test_chain_representations_reject_unknown(write_csv):
    path = write_csv("chain,representation\nA,sausage\n", "chains.csv")
    with pytest.raises(InputError, match="not one of"):
        parse_chain_representations(path)


def test_chain_representations_reject_duplicate(write_csv):
    path = write_csv("chain,representation\nA,cartoon\nA,surface\n", "chains.csv")
    with pytest.raises(InputError, match="duplicate entry"):
        parse_chain_representations(path)


def test_extra_columns_are_ignored(write_csv):
    """A CSV may carry columns of its own -- notes, alternative numberings --
    and they are passed over rather than rejected."""
    text = (
        "chain,residue,notes,color,pdb_numbering,label\n"
        "A,118,Direct contact with DAN at 2.68 A,red,118,Arg118\n"
    )
    coloring = parse_csv(write_csv(text))
    spec = coloring.specs[0]
    assert spec.key == ("A", "118")
    assert spec.colors == {"Default": "#ff0000"}
    assert spec.label == "Arg118"
    # The extra columns reach neither the spec nor the rendered output.
    assert not hasattr(spec, "notes")


def test_extra_column_named_like_a_scheme_is_still_a_scheme(write_csv):
    """'color:' is the scheme prefix, so it is not a free-for-all namespace."""
    coloring = parse_csv(write_csv("chain,residue,color:Escape,notes\nA,5,red,hi\n"))
    assert coloring.scheme_names == ["Escape"]


def test_chain_representations_ignore_extra_columns(write_csv):
    path = write_csv("chain,representation,why\nA,cartoon,legibility\n", "chains.csv")
    assert parse_chain_representations(path) == {"A": "cartoon"}


EXAMPLES_DIR = pathlib.Path(__file__).parent.parent / "examples"

#: Every example directory, so a new one cannot land with an unparseable CSV.
EXAMPLE_DIRS = sorted(p.parent for p in EXAMPLES_DIR.glob("*/command.sh"))


def test_examples_are_discoverable():
    """Guard the glob above: a rename would otherwise make the sweep vacuous."""
    assert EXAMPLE_DIRS, f"no examples/*/command.sh under {EXAMPLES_DIR}"


@pytest.mark.parametrize("example", EXAMPLE_DIRS, ids=lambda p: p.name)
def test_shipped_example_csvs_parse(example):
    """The examples are documentation; their inputs must stay valid."""
    coloring = parse_csv(example / "coloring.csv")
    assert coloring.scheme_names == ["Default"]
    # Persistent labels are only on the short residue-name labels.
    for spec in coloring.specs:
        if spec.show_label:
            assert spec.label is not None

    chains = example / "chains.csv"
    if chains.is_file():
        assert parse_chain_representations(chains)


def test_label_color_and_size_parse(write_csv):
    text = (
        "chain,residue,color,label,show_label,label_color,label_size\n"
        "A,5,red,Arg5,True,navy,4.5\n"
    )
    spec = parse_csv(write_csv(text)).specs[0]
    assert spec.label_color == "#000080"
    assert spec.label_size == 4.5


def test_label_color_and_size_default_to_none(write_csv):
    """The renderer, not the parser, owns the defaults."""
    text = "chain,residue,color,label,show_label\nA,5,red,Arg5,True\n"
    spec = parse_csv(write_csv(text)).specs[0]
    assert spec.label_color is None
    assert spec.label_size is None


@pytest.mark.parametrize("value", ["big", "", "0", "-2"])
def test_bad_label_size_is_fatal(write_csv, value):
    text = (
        "chain,residue,color,label,show_label,label_size\n"
        f"A,5,red,Arg5,True,{value}\n"
    )
    if value == "":
        # Blank means "use the default", not an error.
        assert parse_csv(write_csv(text)).specs[0].label_size is None
        return
    with pytest.raises(InputError, match="line 2, column 'label_size'"):
        parse_csv(write_csv(text))


def test_bad_label_color_is_fatal(write_csv):
    text = (
        "chain,residue,color,label,show_label,label_color\n"
        "A,5,red,Arg5,True,octarine\n"
    )
    with pytest.raises(InputError, match="line 2, column 'label_color'"):
        parse_csv(write_csv(text))


def test_label_style_without_show_label_is_not_an_error(write_csv):
    """Lets a color sit on every row while show_label is toggled during iteration."""
    text = "chain,residue,color,label_color,label_size\nA,5,red,navy,3\n"
    spec = parse_csv(write_csv(text)).specs[0]
    assert spec.show_label is False
    assert spec.label_color == "#000080"
