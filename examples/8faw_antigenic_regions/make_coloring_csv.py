"""Regenerate ``coloring.csv`` for the 8FAW antigenic-regions example.

``coloring.csv`` is committed, and this script is **not** run by
``scripts/build_examples.sh`` or by the tests -- ``command.sh`` reads the
committed file. Run this by hand when the inputs below change::

    .venv/bin/python examples/8faw_antigenic_regions/make_coloring_csv.py

It exists because the ~490 rows are derived from two external sources, and a
table that large is only auditable if its derivation ships with it.

Two things the script fetches rather than hard-codes:

* the lab's H3N2 site-numbering map, which is what turns a residue number into
  an HA1 or HA2 site number;
* PDB 8FAW itself, so that only *modeled* residues get a row.

The numbering frame is the load-bearing assumption here, so it is asserted
rather than trusted: if a revised map or a different entry ever shifts it, this
script fails instead of writing a plausible-looking but wrong CSV.
"""

import csv
import io
import pathlib
import urllib.request

import gemmi

#: Author numbering in 8FAW is a single chain running across HA1 and HA2, which
#: is the same frame as this map's ``sequential_site``.
NUMBERING_MAP_URL = (
    "https://raw.githubusercontent.com/jbloomlab/flu-seqneut-2026/main/data/"
    "nextstrain-prot-titers-tree_data/H3N2_site_numbering_map.tsv"
)

PDB_ID = "8FAW"
STRUCTURE_URL = f"https://files.rcsb.org/download/{PDB_ID}.cif"

#: The polymer. 8FAW's asymmetric unit is one protomer; the trimer is assembly 1.
POLYMER_CHAIN = "A"

#: The LSTc receptor analogue, Neu5Ac-a2,6-Gal-b1,4-GlcNAc-b1,3-Gal-b1,4-Glc,
#: reducing end first. Naming a sugar in the CSV is what replaces its 3D-SNFG
#: symbols with a plain colored ball-and-stick. Every sugar in the entry is named
#: here -- the receptor analogue and the host N-glycans alike -- so nothing is
#: left to the --glycans default.
RECEPTOR_CHAIN = "D"

#: Antigenic sites A-E of H3 HA1, from Table 2 ("Amino acids assigned to
#: antigenic sites") of Stray & Pittman, Virol J 2012;9:91, PMC3499391.
#: Footnote h of that table: "H3 HA residues numbered as for mature HA1 of
#: A/Aichi/2/1968". Footnote g: residues the table encloses in parentheses were
#: assigned in previous studies but did not meet the authors' own inclusion
#: criteria. Both kinds are included here -- this is the conventional full
#: definition of the five sites, and the distinction is about how the 2012
#: authors scored evolutionary rates, not about whether antibodies bind there.
SITES = {
    "A": [
        121,
        122,
        123,
        124,
        125,
        126,
        127,
        129,
        131,
        132,
        133,
        134,
        135,
        136,
        137,
        138,
        140,
        142,
        143,
        144,
        145,
        146,
    ],
    "B": [
        155,
        156,
        157,
        158,
        159,
        160,
        186,
        188,
        189,
        190,
        192,
        193,
        194,
        196,
        197,
        198,
        199,
        246,
        247,
    ],
    "C": [49, 50, 53, 54, 271, 273, 275, 276, 278],
    "D": [
        167,
        201,
        202,
        203,
        204,
        205,
        206,
        207,
        214,
        216,
        217,
        218,
        219,
        220,
        222,
        223,
        225,
        226,
        227,
        242,
    ],
    "E": [62, 63, 75, 78, 79, 80, 81, 82, 83, 91, 92, 94],
}

#: Colorblind-safe qualitative palette. Deliberately not the colors of the
#: paper's own figure, whose yellow site B would be illegible against the pale
#: gray used for the rest of the surface.
SITE_COLORS = {
    "A": "#e41a1c",
    "B": "#377eb8",
    "C": "#4daf4a",
    "D": "#984ea3",
    "E": "#ff7f00",
}

#: The two grays are not decoration: they draw the HA1/HA2 boundary, which is
#: what the _HA1 and _HA2 label suffixes exist to tell you about.
HA1_COLOR = "#e8e8e8"
HA2_COLOR = "#bdbdbd"
RECEPTOR_COLOR = "#000000"
GLYCAN_COLOR = "#ffd700"

#: Label text sits on top of a residue already painted its site color, so it
#: must not inherit that color. The size is below the 2.0 default because the
#: trimer draws every one of these labels three times.
LABEL_COLOR = "#252525"
LABEL_SIZE = "1.6"

CITATION = "Stray & Pittman 2012 Virol J 9:91"

#: Residues whose identity fixes the numbering frame. The four aromatics line
#: the receptor-binding site and the nine cysteines form HA1's disulfides; all
#: are invariant across H3 and all are quoted in H3 HA1 numbering.
FRAME_CHECKS = {
    98: "TYR",
    153: "TRP",
    183: "HIS",
    195: "TYR",
    14: "CYS",
    52: "CYS",
    64: "CYS",
    76: "CYS",
    97: "CYS",
    139: "CYS",
    277: "CYS",
    281: "CYS",
    305: "CYS",
}

HEADER = [
    "chain",
    "residue",
    "color",
    "label",
    "show_label",
    "representation",
    "label_color",
    "label_size",
    "notes",
]


def load_numbering_map():
    """Return ``{sequential_site: (protein, protein_site)}`` from the lab's map."""
    with urllib.request.urlopen(NUMBERING_MAP_URL) as response:
        text = response.read().decode()
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    return {
        int(row["sequential_site"]): (row["protein"], int(row["protein_site"]))
        for row in reader
    }


def load_structure():
    """Return the 8FAW model, fetched from RCSB."""
    with urllib.request.urlopen(STRUCTURE_URL) as response:
        text = response.read().decode()
    structure = gemmi.make_structure_from_block(
        gemmi.cif.read_string(text).sole_block()
    )
    structure.setup_entities()
    return structure[0]


def partition_residues(model):
    """Split the modeled residues into polymer, host glycans and receptor.

    gemmi splits waters and heteroatoms into a second chain reusing the author
    ID, so the polymer and the two N-glycans that hang off it both appear under
    chain A. Classify by component rather than by chain: amino acids on the
    polymer chain are the protein, everything on the receptor chain is the
    receptor, and every other non-water residue is a host glycan.

    Returns three ``[(chain, residue_number, component_name), ...]`` lists.
    """
    polymer, glycans, receptor = [], [], []
    for chain in model:
        for residue in chain:
            info = gemmi.find_tabulated_residue(residue.name)
            if info is not None and info.is_water():
                continue
            entry = (chain.name, residue.seqid.num, residue.name)
            if chain.name == RECEPTOR_CHAIN:
                receptor.append(entry)
            elif (
                chain.name == POLYMER_CHAIN
                and info is not None
                and info.is_amino_acid()
            ):
                polymer.append(entry)
            else:
                glycans.append(entry)
    if not polymer:
        raise SystemExit(f"{PDB_ID} has no polymer on chain {POLYMER_CHAIN!r}")
    if not receptor:
        raise SystemExit(f"{PDB_ID} has no receptor on chain {RECEPTOR_CHAIN!r}")
    return polymer, glycans, receptor


def check_frame(polymer):
    """Fail loudly if author numbering is not H3 HA1 numbering after all."""
    seen = {number: component for _, number, component in polymer}
    wrong = {
        num: (expected, seen.get(num))
        for num, expected in FRAME_CHECKS.items()
        if seen.get(num) != expected
    }
    if wrong:
        raise SystemExit(
            f"{PDB_ID} chain {POLYMER_CHAIN} is not in H3 HA1 numbering: "
            + "; ".join(
                f"expected {exp} at {num}, found {got}"
                for num, (exp, got) in sorted(wrong.items())
            )
        )


def check_sites():
    """Fail loudly if the transcribed site definitions have drifted."""
    flat = [site for residues in SITES.values() for site in residues]
    if len(flat) != len(set(flat)):
        raise SystemExit("antigenic sites overlap; they are disjoint in Table 2")
    if len(flat) != 82:
        raise SystemExit(f"expected 82 antigenic-site residues, got {len(flat)}")


def site_of(residue_number):
    """Return the antigenic site containing this HA1 site, or ``None``."""
    for site, residues in SITES.items():
        if residue_number in residues:
            return site
    return None


def polymer_rows(polymer, numbering):
    """One row per modeled polymer residue, colored by antigenic site."""
    ha2_offset = max(
        seq for seq, (protein, _) in numbering.items() if protein == "HA2"
    ) - max(site for protein, site in numbering.values() if protein == "HA2")
    rows = []
    for _, number, _component in polymer:
        if number in numbering:
            protein, site = numbering[number]
        else:
            # The map stops one residue short of what 8FAW models. Extend it by
            # its own constant HA2 offset rather than dropping the residue,
            # which would leave the HA2 C-terminus uncolored and unlabeled.
            protein, site = "HA2", number - ha2_offset
            print(
                f"note: residue {number} is past the end of the numbering map; "
                f"assigning {site}_{protein} by the map's own HA2 offset "
                f"of {ha2_offset}"
            )
        region = site_of(site) if protein == "HA1" else None
        # One label for every residue, antigenic site or not: the site number
        # alone is ambiguous across HA1 and HA2, and this is both the mouseover
        # text and, on an antigenic-site residue, the text drawn into the scene.
        label = f"{site}_{protein}"
        if region is not None:
            rows.append(
                [
                    POLYMER_CHAIN,
                    number,
                    SITE_COLORS[region],
                    label,
                    "True",
                    "",
                    LABEL_COLOR,
                    LABEL_SIZE,
                    f"HA1 site {site}; antigenic site {region} of {CITATION}",
                ]
            )
        else:
            rows.append(
                [
                    POLYMER_CHAIN,
                    number,
                    HA1_COLOR if protein == "HA1" else HA2_COLOR,
                    label,
                    "",
                    "",
                    "",
                    "",
                    f"{protein} site {site}; not in a defined antigenic site",
                ]
            )
    return rows


def receptor_rows(receptor):
    """One row per LSTc sugar, with the assembled name drawn on the last one."""
    rows = []
    for index, (_, number, component) in enumerate(receptor, start=1):
        last = index == len(receptor)
        rows.append(
            [
                RECEPTOR_CHAIN,
                number,
                RECEPTOR_COLOR,
                "LSTc" if last else component,
                "True" if last else "",
                "ball-and-stick",
                LABEL_COLOR if last else "",
                LABEL_SIZE if last else "",
                f"LSTc sugar {index} of {len(receptor)} ({component}); "
                "named here so it is drawn in this color rather than as an SNFG symbol",
            ]
        )
    return rows


def glycan_rows(glycans):
    """One row per host N-glycan sugar, drawn in one color rather than as SNFG.

    These are not labeled: several shield an antigenic region, which is the
    point of showing them, and adding a dozen more labels to a view that
    already draws 83 per protomer would obscure the thing they shield.
    """
    return [
        [
            chain,
            number,
            GLYCAN_COLOR,
            component,
            "",
            "ball-and-stick",
            "",
            "",
            f"Host N-glycan sugar ({component}); named here so it is drawn in "
            "this color rather than as an SNFG symbol",
        ]
        for chain, number, component in sorted(glycans)
    ]


def main():
    check_sites()
    numbering = load_numbering_map()
    model = load_structure()

    polymer, glycans, receptor = partition_residues(model)
    check_frame(polymer)

    # Ordered so the file sorts by chain then residue, which is also what the
    # docs' snippet line range depends on: the polymer block starts on line 2.
    rows = (
        polymer_rows(polymer, numbering)
        + glycan_rows(glycans)
        + receptor_rows(receptor)
    )

    out_path = pathlib.Path(__file__).parent / "coloring.csv"
    with out_path.open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)

    labeled = sum(1 for row in rows if row[4] == "True")
    print(
        f"wrote {out_path} ({len(rows)} rows: {len(polymer)} polymer, "
        f"{len(glycans)} host glycan, {len(receptor)} receptor; "
        f"{labeled} with a drawn label)"
    )


if __name__ == "__main__":
    main()
