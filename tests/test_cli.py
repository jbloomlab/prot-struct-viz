"""Tests for the CLI: exit codes, and that the report is always written."""

import textwrap

import pytest
import yaml
from click.testing import CliRunner

from prot_struct_viz.cli import main

CSV = """chain,residue,color,label,show_label
A,412A,#d62728,site 412A,True
A,0,#9467bd,the DANA ligand,
"""

#: A CSV naming every addressable residue would be unwieldy here, so the
#: mismatch-mode tests use this partial CSV and assert the direction that fires.

#: The per-view keys the spec requires. Every view needs all of them, which is
#: what YAML anchors are for; ``test_anchors_supply_the_shared_view_keys`` covers
#: that shape, and the fixture below just writes them out.
BASE_VIEW = {
    "default_color": "#d9d9d9",
    "default_representation": "cartoon",
    "waters": "hide",
    "ligands": "show",
    "glycans": "snfg",
    "ions": "show",
}


def _run(args):
    return CliRunner().invoke(main, args)


@pytest.fixture
def write_spec(tmp_path, write_csv, fixture_cif):
    """Write a spec file and return its path.

    ``views`` are dicts of whatever each view sets beyond `BASE_VIEW`.
    """

    def _write(
        out_name="view.html",
        views=None,
        *,
        csv=None,
        name="spec.yaml",
        **shared,
    ):
        csv = csv if csv is not None else write_csv(CSV)
        views = views if views is not None else [{}]
        document = {
            "structure": str(fixture_cif),
            "out": str(tmp_path / out_name),
            "assembly": "au",
            "on_mismatch": "report",
            **shared,
            "views": [
                {"name": f"View {index}", "csv": str(csv), **BASE_VIEW, **view}
                for index, view in enumerate(views)
            ],
        }
        path = tmp_path / name
        path.write_text(yaml.safe_dump(document, sort_keys=False))
        return path

    return _write


def test_report_mode_succeeds(tmp_path, write_spec):
    result = _run([str(write_spec())])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "view.html").is_file()
    assert (tmp_path / "view_report.txt").is_file()


def test_progress_goes_to_stdout_and_the_report(tmp_path, write_spec):
    result = _run([str(write_spec())])
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
def test_mismatch_modes(tmp_path, write_spec, mode, expected_exit):
    spec = write_spec(f"{mode}.html", on_mismatch=mode)
    result = _run([str(spec)])
    assert result.exit_code == expected_exit, result.output
    # The report is written in every mode, including the fatal ones.
    assert (tmp_path / f"{mode}_report.txt").is_file()
    assert (tmp_path / f"{mode}.html").is_file() is (expected_exit == 0)


def test_extra_in_csv_is_fatal_in_its_mode(tmp_path, write_spec, write_csv):
    spec = write_spec(
        csv=write_csv("chain,residue,color\nZ,1,red\n"),
        on_mismatch="error-extra-in-csv",
    )
    result = _run([str(spec)])
    assert result.exit_code == 1
    assert (tmp_path / "view_report.txt").is_file()


def test_bad_out_suffix_exits_nonzero(write_spec):
    result = _run([str(write_spec("view.htm"))])
    assert result.exit_code == 1
    assert "must end in '.html'" in result.output


def test_bad_csv_exits_nonzero_and_names_the_line(tmp_path, write_spec, write_csv):
    spec = write_spec(csv=write_csv("chain,residue,color\nA,100,notacolor\n"))
    result = _run([str(spec)])
    assert result.exit_code == 1
    assert "line 2" in result.output
    # The report still records the progress made before the CSV was read.
    assert (tmp_path / "view_report.txt").is_file()


def test_unknown_assembly_exits_nonzero(write_spec):
    result = _run([str(write_spec(assembly="7"))])
    assert result.exit_code == 1
    assert "not defined by this structure" in result.output


def test_chain_subset(write_spec, write_csv):
    spec = write_spec(
        views=[{"chains": ["B", "C"]}],
        csv=write_csv("chain,residue,color\nB,1,red\n"),
    )
    result = _run([str(spec)])
    assert result.exit_code == 0, result.output
    assert "chains displayed: ['B', 'C']" in result.output


def test_unknown_chain_exits_nonzero(write_spec):
    result = _run([str(write_spec(views=[{"chains": ["Z"]}]))])
    assert result.exit_code == 1
    assert "not in the structure" in result.output


def test_hetero_settings_reach_the_report(write_spec):
    spec = write_spec(views=[{"waters": "show", "glycans": "hide", "ions": "hide"}])
    result = _run([str(spec)])
    assert result.exit_code == 0, result.output
    assert "waters=show" in result.output
    assert "glycans=hide" in result.output
    assert "ions=hide" in result.output


def test_hetero_settings_are_per_view(write_spec):
    """The point of the format: two views of one structure, drawn differently."""
    spec = write_spec(views=[{"glycans": "snfg"}, {"glycans": "hide"}])
    result = _run([str(spec)])
    assert result.exit_code == 0, result.output
    assert "glycans=snfg" in result.output
    assert "glycans=hide" in result.output
    assert result.output.count("=== view:") == 2


def test_chain_representation_file(write_spec, write_csv):
    chains = write_csv("chain,representation\nA,surface\n", "chains.csv")
    spec = write_spec(views=[{"chain_representation": str(chains)}])
    result = _run([str(spec)])
    assert result.exit_code == 0, result.output
    assert "per-chain representations: {'A': 'surface'}" in result.output


def test_chains_does_not_change_validation(write_spec, write_csv):
    """A view's chains subset its display; validation still sees the whole model."""
    spec = write_spec(
        views=[{"chains": ["B"]}],
        csv=write_csv("chain,residue,color\nB,1,red\nA,100,blue\n"),
        on_mismatch="error-extra-in-csv",
    )
    result = _run([str(spec)])
    # A/100 is a real residue, so error-extra-in-csv must not fire just because
    # chain A is not being drawn.
    assert result.exit_code == 0, result.output
    assert "name residues on chains this view excludes" in result.output


def test_bad_spec_exits_nonzero(tmp_path):
    spec = tmp_path / "spec.yaml"
    spec.write_text("structure: 1F8B\n")
    result = _run([str(spec)])
    assert result.exit_code == 1
    assert "missing top-level" in result.output


def test_missing_spec_file_exits_nonzero(tmp_path):
    result = _run([str(tmp_path / "absent.yaml")])
    assert result.exit_code == 2  # click rejects the argument before we see it


def test_anchors_supply_the_shared_view_keys(tmp_path, write_csv, fixture_cif):
    """The format has no defaults, so anchors are how repetition is avoided.

    This is the shape the docs recommend, written out literally rather than
    dumped, because it is the merge key that is under test.
    """
    csv = write_csv(CSV)
    spec = tmp_path / "spec.yaml"
    spec.write_text(textwrap.dedent(f"""\
            structure: {fixture_cif}
            out: {tmp_path / "view.html"}
            assembly: au
            on_mismatch: report

            definitions:
              base: &base
                default_color: "#d9d9d9"
                default_representation: cartoon
                waters: hide
                ligands: show
                glycans: snfg
                ions: show

            views:
              - <<: *base
                name: Surface
                csv: {csv}
                default_representation: surface
              - <<: *base
                name: No glycans
                csv: {csv}
                glycans: hide
            """))
    result = _run([str(spec)])
    assert result.exit_code == 0, result.output
    # The merge supplied the keys neither view states, and each view's own key
    # still wins over the merged one.
    assert "base representation: surface" in result.output
    assert "base representation: cartoon" in result.output
    assert "glycans=hide" in result.output
