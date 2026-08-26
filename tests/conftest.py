"""Shared fixtures: the trimmed structure and CSVs written per test."""

import pathlib

import pytest

from prot_struct_viz import structure as structure_module

DATA_DIR = pathlib.Path(__file__).parent / "data"

#: The trimmed 1F8B entry. See tests/data/README.md.
FIXTURE_CIF = DATA_DIR / "1f8b_trimmed.cif"


@pytest.fixture(scope="session")
def fixture_cif():
    return FIXTURE_CIF


@pytest.fixture(scope="session")
def coordinate_text():
    return FIXTURE_CIF.read_text()


@pytest.fixture(scope="session")
def structure(coordinate_text):
    return structure_module.load_structure(coordinate_text, "mmcif")


@pytest.fixture(scope="session")
def deposited(structure):
    return structure_module.get_deposited_residues(structure)


@pytest.fixture
def write_csv(tmp_path):
    """Write CSV text to a temp file and return its path."""

    def _write(text, name="coloring.csv"):
        path = tmp_path / name
        path.write_text(text)
        return path

    return _write
