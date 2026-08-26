"""Trim the deposited 1F8B mmCIF down to the test fixture.

Run by hand, not by the test suite; its output (``1f8b_trimmed.cif``) is
committed. Keeps all polymer, glycan, ligand, and ion residues and only the
first few waters, so the fixture exercises every residue class and the
insertion-coded sites while staying small.

    python tests/data/_make_fixture.py <deposited 1F8B.cif> tests/data/1f8b_trimmed.cif
"""

import sys

import gemmi

KEEP_WATERS = 8


def main(source: str, dest: str) -> None:
    structure = gemmi.read_structure(source)
    structure.setup_entities()
    kept_waters = 0
    for model in structure:
        for chain in model:
            drop = []
            for index, residue in enumerate(chain):
                if residue.name != "HOH":
                    continue
                if kept_waters < KEEP_WATERS:
                    kept_waters += 1
                else:
                    drop.append(index)
            # Delete from the end so earlier indices stay valid.
            for index in reversed(drop):
                del chain[index]
    structure.setup_entities()
    structure.make_mmcif_document().write_file(dest)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
