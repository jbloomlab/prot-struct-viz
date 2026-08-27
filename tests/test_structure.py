"""Tests for loading structures and enumerating deposited residues."""

import collections

import pytest

from prot_struct_viz._config import InputError
from prot_struct_viz.structure import (
    addressable_residues,
    assembly_names,
    get_assembly_chains,
    get_deposited_residues,
    load_structure,
    residue_counts,
    resolve_structure,
)


def test_resolve_local_file(fixture_cif):
    text, fmt = resolve_structure(str(fixture_cif))
    assert fmt == "mmcif"
    assert text.startswith("data_")


def test_resolve_rejects_non_id_non_path():
    with pytest.raises(InputError, match="neither an existing file nor a PDB ID"):
        resolve_structure("not a structure")


def test_resolve_rejects_unknown_suffix(tmp_path):
    path = tmp_path / "coords.xyzzy"
    path.write_text("nonsense")
    with pytest.raises(InputError, match="cannot tell the format"):
        resolve_structure(str(path))


def test_all_residue_classes_present(deposited):
    counts = collections.Counter(deposited.values())
    # The fixture was chosen so every class the code distinguishes appears.
    assert set(counts) == {"polymer", "glycan", "ligand", "ion", "water"}


def test_insertion_codes_preserved(deposited):
    assert ("A", "169A") in deposited
    assert ("A", "412A") in deposited
    assert ("A", "412B") in deposited
    # The bare number is a different residue from the insertion-coded one.
    assert ("A", "412") in deposited
    assert deposited[("A", "169A")] == "polymer"


def test_classification_of_specific_residues(deposited):
    assert deposited[("A", "0")] == "ligand"  # DANA inhibitor
    assert deposited[("A", "998")] == "ion"  # Ca2+
    assert deposited[("B", "1")] == "glycan"  # branched entity
    assert deposited[("A", "1146")] == "glycan"  # lone NAG, caught by sugar kind
    assert deposited[("A", "1147")] == "water"


def test_addressable_excludes_only_water(deposited):
    addressable = addressable_residues(deposited)
    waters = {k for k, v in deposited.items() if v == "water"}
    assert waters
    assert addressable == set(deposited) - waters


def test_residue_counts_cover_every_residue(structure, deposited):
    counts = residue_counts(structure)
    assert sum(counts.values()) == len(deposited)
    assert set(counts) == {"A", "B", "C"}


def test_chain_subset(structure):
    subset = get_deposited_residues(structure, ["B"])
    assert {chain for chain, _ in subset} == {"B"}
    assert residue_counts(structure, ["B"]) == {"B": 7}


def test_unknown_chain_is_fatal(structure):
    with pytest.raises(InputError, match="not in the structure"):
        get_deposited_residues(structure, ["Z"])


def test_assembly_chains(structure):
    assert assembly_names(structure) == ["1"]
    # Assembly generators name subchains; they map back to author chain IDs.
    assert get_assembly_chains(structure, "1") == {"A", "B", "C"}
    assert get_assembly_chains(structure, "au") is None


def test_unknown_assembly_is_fatal(structure):
    with pytest.raises(InputError, match="not defined by this structure"):
        get_assembly_chains(structure, "7")


def test_no_models_is_fatal():
    with pytest.raises(InputError):
        load_structure("data_empty\n", "mmcif")


@pytest.mark.network
def test_fetch_from_rcsb():
    text, fmt = resolve_structure("1F8B")
    assert fmt == "mmcif"
    # Enough of the entry to prove we got mmCIF for the right structure, not an
    # RCSB error page (which would also decode cleanly).
    assert text.startswith("data_1F8B")
    assert "_atom_site." in text
