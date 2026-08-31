# Test data

## `1f8b_trimmed.cif`

Influenza B/Beijing/1/87 neuraminidase with the inhibitor DANA, trimmed to serve
as the test fixture. It is used because a single small entry exercises every
residue class the code distinguishes (polymer, glycan, ligand, ion, water),
carries three insertion-coded sites (A/169A, A/412A, A/412B), and defines a
tetrameric assembly built from crystal symmetry operations rather than deposited
copies.

- Source: <https://files.rcsb.org/download/1F8B.cif>
- Downloaded: 2026-08-26
- Trimmed with [`make_fixture.py`](make_fixture.py), which drops every water past
  the first `KEEP_WATERS` and rewrites the file with gemmi. It is a gemmi rewrite
  rather than a subset of the deposited lines, so re-running it on a different
  gemmi will not reproduce this file byte for byte; the fixture in git is the
  reference.
