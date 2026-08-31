"""Tests for mismatch detection, the four on_mismatch modes, and the report."""

import pytest

from prot_struct_viz._config import InputError
from prot_struct_viz.report import Reporter, report_path_for
from prot_struct_viz.residues import parse_csv
from prot_struct_viz.structure import addressable_residues
from prot_struct_viz.validate import validate


def _coloring_for(write_csv, keys):
    """A CSV naming exactly ``keys``, all colored red."""
    rows = "\n".join(f"{chain},{residue},red" for chain, residue in keys)
    return parse_csv(write_csv(f"chain,residue,color\n{rows}\n"))


@pytest.fixture
def complete_coloring(write_csv, deposited):
    """A CSV naming every addressable residue, so there is no mismatch."""
    return _coloring_for(write_csv, sorted(addressable_residues(deposited)))


def test_no_mismatch(complete_coloring, deposited):
    report = validate(complete_coloring, deposited, None)
    assert not report.in_csv_not_structure
    assert not report.in_structure_not_csv
    assert not report.in_csv_not_in_assembly
    for mode in ("error-any", "error-extra-in-pdb", "error-extra-in-csv", "report"):
        assert report.is_fatal(mode) is False


def test_extra_in_csv(write_csv, deposited):
    coloring = _coloring_for(write_csv, [("A", "169A"), ("Z", "1")])
    report = validate(coloring, deposited, None)
    assert report.in_csv_not_structure == {("Z", "1")}
    assert report.in_structure_not_csv  # nearly everything
    assert report.is_fatal("error-extra-in-csv") is True
    assert report.is_fatal("error-any") is True
    assert report.is_fatal("report") is False


def test_extra_in_pdb_only(write_csv, deposited):
    coloring = _coloring_for(write_csv, [("A", "169A")])
    report = validate(coloring, deposited, None)
    assert not report.in_csv_not_structure
    assert report.in_structure_not_csv
    assert report.is_fatal("error-extra-in-pdb") is True
    assert report.is_fatal("error-extra-in-csv") is False
    assert report.is_fatal("error-any") is True


def test_extra_in_csv_tolerated_by_extra_in_pdb_mode(deposited, write_csv):
    keys = sorted(addressable_residues(deposited)) + [("Z", "1")]
    coloring = _coloring_for(write_csv, keys)
    report = validate(coloring, deposited, None)
    assert report.in_csv_not_structure == {("Z", "1")}
    assert not report.in_structure_not_csv
    # error-extra-in-pdb only cares about the structure side.
    assert report.is_fatal("error-extra-in-pdb") is False
    assert report.is_fatal("error-extra-in-csv") is True


def test_waters_never_flood_the_report(complete_coloring, deposited):
    """A complete CSV needs no water rows, because waters are not addressable."""
    report = validate(complete_coloring, deposited, None)
    waters = {k for k, v in deposited.items() if v == "water"}
    assert waters
    assert not (report.in_structure_not_csv & waters)


def test_csv_row_on_a_water_gets_targeted_message(write_csv, deposited):
    water = sorted(k for k, v in deposited.items() if v == "water")[0]
    coloring = _coloring_for(write_csv, [water])
    report = validate(coloring, deposited, None)
    assert report.csv_targets_water == {water}
    assert water in report.in_csv_not_structure
    text = report.format()
    assert "targets a water residue" in text
    assert "'waters' key" in text
    assert "no such residue" not in text


def test_assembly_subset_warning(write_csv, deposited):
    coloring = _coloring_for(write_csv, [("A", "169A"), ("B", "1")])
    # An assembly that omits chain B.
    report = validate(coloring, deposited, {"A"})
    assert report.in_csv_not_in_assembly == {("B", "1")}
    # Never fatal on its own.
    assert report.is_fatal("error-extra-in-csv") is False
    assert "absent from the chosen assembly: 1" in report.format()


def test_asymmetric_unit_has_no_assembly_warning(write_csv, deposited):
    coloring = _coloring_for(write_csv, [("A", "169A"), ("B", "1")])
    report = validate(coloring, deposited, None)
    assert not report.in_csv_not_in_assembly


def test_report_groups_by_residue_class(write_csv, deposited):
    coloring = _coloring_for(write_csv, [("A", "169A")])
    text = validate(coloring, deposited, None).format()
    for residue_class in ("polymer", "ligand", "glycan", "ion"):
        assert f"{residue_class} (" in text
    assert "water (" not in text


def test_is_fatal_rejects_an_unknown_mode(complete_coloring, deposited):
    """Without the guard, an unhandled mode falls through to error-extra-in-csv."""
    report = validate(complete_coloring, deposited, None)
    with pytest.raises(InputError, match="unknown on_mismatch mode"):
        report.is_fatal("lenient")


def test_report_path_for():
    import pathlib

    assert report_path_for(pathlib.Path("figure.html")) == pathlib.Path(
        "figure_report.txt"
    )
    assert report_path_for(pathlib.Path("out/fig.HTML")) == pathlib.Path(
        "out/fig_report.txt"
    )


def test_report_path_requires_html():
    import pathlib

    with pytest.raises(InputError, match="must end in '.html'"):
        report_path_for(pathlib.Path("figure.htm"))


def test_reporter_writes_to_both_sinks(tmp_path, capsys):
    path = tmp_path / "fig_report.txt"
    with Reporter(path) as reporter:
        reporter.log("structure: 1F8B")
        reporter.log("chains: A, B, C")
    captured = capsys.readouterr().out
    written = path.read_text()
    assert "structure: 1F8B" in captured
    assert "structure: 1F8B" in written
    assert "chains: A, B, C" in written


def test_reporter_file_exists_after_an_error(tmp_path):
    """The report survives an abort part-way through, which is its whole point."""
    path = tmp_path / "fig_report.txt"
    reporter = Reporter(path)
    try:
        reporter.log("progress so far")
        raise InputError("something failed")
    except InputError:
        pass
    finally:
        reporter.close()
    assert "progress so far" in path.read_text()


def test_display_path_is_relative_under_the_working_directory(tmp_path, monkeypatch):
    import pathlib

    from prot_struct_viz.report import display_path

    monkeypatch.chdir(tmp_path)
    nested = tmp_path / "results" / "view.html"
    assert display_path(nested) == str(pathlib.Path("results/view.html"))


def test_display_path_stays_absolute_outside_the_working_directory(
    tmp_path, monkeypatch
):
    import pathlib

    from prot_struct_viz.report import display_path

    inner = tmp_path / "inner"
    inner.mkdir()
    monkeypatch.chdir(inner)
    outside = tmp_path / "view.html"
    # Better the full path than a chain of '..'.
    assert display_path(outside) == str(outside)
    assert not pathlib.Path(display_path(outside)).is_relative_to(inner)
