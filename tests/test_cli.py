"""Tests for the CLI: exit codes, and that the report is always written."""

import pytest
from click.testing import CliRunner

from prot_struct_viz.cli import main

CSV = """chain,residue,color,label,show_label
A,412A,#d62728,site 412A,True
A,0,#9467bd,the DANA ligand,
"""

#: A CSV naming every addressable residue would be unwieldy here, so the
#: mismatch-mode tests use this partial CSV and assert the direction that fires.


def _run(args):
    return CliRunner().invoke(main, args)


@pytest.fixture
def base_args(tmp_path, write_csv, fixture_cif):
    csv = write_csv(CSV)

    def _args(out_name="view.html", *extra):
        return [
            "--structure",
            str(fixture_cif),
            "--csv",
            str(csv),
            "--out",
            str(tmp_path / out_name),
            *extra,
        ]

    return _args


def test_report_mode_succeeds(tmp_path, base_args):
    result = _run(base_args())
    assert result.exit_code == 0, result.output
    assert (tmp_path / "view.html").is_file()
    assert (tmp_path / "view_report.txt").is_file()


def test_progress_goes_to_stdout_and_the_report(tmp_path, base_args):
    result = _run(base_args())
    report = (tmp_path / "view_report.txt").read_text()
    assert "chains found:" in result.output
    assert "chains found:" in report
    assert "Mismatch report" in report


@pytest.mark.parametrize(
    "mode,expected_exit",
    [
        ("report", 0),
        # The structure has residues the CSV omits, so these two fire.
        ("error-any", 1),
        ("error-extra-in-pdb", 1),
        # The CSV names nothing absent from the structure, so this one does not.
        ("error-extra-in-csv", 0),
    ],
)
def test_mismatch_modes(tmp_path, base_args, mode, expected_exit):
    result = _run(base_args(f"{mode}.html", "--on-mismatch", mode))
    assert result.exit_code == expected_exit, result.output
    # The report is written in every mode, including the fatal ones.
    assert (tmp_path / f"{mode}_report.txt").is_file()
    assert (tmp_path / f"{mode}.html").is_file() is (expected_exit == 0)


def test_extra_in_csv_is_fatal_in_its_mode(tmp_path, write_csv, fixture_cif):
    csv = write_csv("chain,residue,color\nZ,1,red\n")
    result = _run(
        [
            "--structure",
            str(fixture_cif),
            "--csv",
            str(csv),
            "--out",
            str(tmp_path / "view.html"),
            "--on-mismatch",
            "error-extra-in-csv",
        ]
    )
    assert result.exit_code == 1
    assert (tmp_path / "view_report.txt").is_file()


def test_bad_out_suffix_exits_nonzero(tmp_path, base_args):
    result = _run(base_args("view.htm"))
    assert result.exit_code == 1
    assert "must end in '.html'" in result.output


def test_bad_csv_exits_nonzero_and_names_the_line(tmp_path, write_csv, fixture_cif):
    csv = write_csv("chain,residue,color\nA,100,notacolor\n")
    result = _run(
        [
            "--structure",
            str(fixture_cif),
            "--csv",
            str(csv),
            "--out",
            str(tmp_path / "view.html"),
        ]
    )
    assert result.exit_code == 1
    assert "line 2" in result.output
    # The report still records the progress made before the CSV was read.
    assert (tmp_path / "view_report.txt").is_file()


def test_unknown_assembly_exits_nonzero(tmp_path, base_args):
    result = _run(base_args("view.html", "--assembly", "7"))
    assert result.exit_code == 1
    assert "not defined by this structure" in result.output


def test_chain_subset(tmp_path, write_csv, fixture_cif):
    csv = write_csv("chain,residue,color\nB,1,red\n")
    result = _run(
        [
            "--structure",
            str(fixture_cif),
            "--csv",
            str(csv),
            "--out",
            str(tmp_path / "view.html"),
            "--chains",
            "B,C",
        ]
    )
    assert result.exit_code == 0, result.output
    assert "chains displayed: ['B', 'C']" in result.output


def test_unknown_chain_exits_nonzero(tmp_path, base_args):
    result = _run(base_args("view.html", "--chains", "Z"))
    assert result.exit_code == 1
    assert "not in the structure" in result.output


def test_hetero_flags_reach_the_report(tmp_path, base_args):
    result = _run(
        base_args(
            "view.html", "--waters", "show", "--glycans", "hide", "--ions", "hide"
        )
    )
    assert result.exit_code == 0, result.output
    assert "waters=show" in result.output
    assert "glycans=hide" in result.output
    assert "ions=hide" in result.output


def test_chain_representation_file(tmp_path, base_args, write_csv):
    chains = write_csv("chain,representation\nA,surface\n", "chains.csv")
    result = _run(base_args("view.html", "--chain-representation", str(chains)))
    assert result.exit_code == 0, result.output
    assert "per-chain representations: {'A': 'surface'}" in result.output


def test_multi_scheme_warns_about_unselectable_schemes(
    tmp_path, write_csv, fixture_cif
):
    csv = write_csv("chain,residue,color:Entropy,color:Escape\nA,100,red,blue\n")
    result = _run(
        [
            "--structure",
            str(fixture_cif),
            "--csv",
            str(csv),
            "--out",
            str(tmp_path / "view.html"),
        ]
    )
    assert result.exit_code == 0, result.output
    assert "coloring by scheme 'Entropy'" in result.output
    assert "not yet selectable" in result.output


def test_chains_does_not_change_validation(tmp_path, write_csv, fixture_cif):
    """--chains subsets the display; validation still sees the whole model."""
    csv = write_csv("chain,residue,color\nB,1,red\nA,100,blue\n")
    result = _run(
        [
            "--structure",
            str(fixture_cif),
            "--csv",
            str(csv),
            "--out",
            str(tmp_path / "view.html"),
            "--chains",
            "B",
            "--on-mismatch",
            "error-extra-in-csv",
        ]
    )
    # A/100 is a real residue, so error-extra-in-csv must not fire just because
    # chain A is not being drawn.
    assert result.exit_code == 0, result.output
    assert "name residues on chains that --chains excludes" in result.output
