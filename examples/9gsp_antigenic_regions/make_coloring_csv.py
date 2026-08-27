"""Regenerate ``coloring.csv`` for the 9GSP antigenic-regions example.

``coloring.csv`` is committed, and this script is **not** run by
``scripts/build_examples.sh`` or by the tests -- ``command.sh`` reads the
committed file. Run this by hand when the inputs below change::

    .venv/bin/python examples/9gsp_antigenic_regions/make_coloring_csv.py

This is the H1 counterpart of the 8FAW script next door, and follows it
closely; the differences are all consequences of the entry. 9GSP deposits the
whole trimer rather than one protomer, so the annotation covers three chains
instead of relying on symmetry, and nothing is bound to the receptor site.

Two things the script fetches rather than hard-codes:

* the lab's H1N1 site-numbering map, which is what splits a residue number into
  an HA1 or HA2 site number;
* PDB 9GSP itself, so that only *modeled* residues get a row.

The numbering frame is the load-bearing assumption here, so it is asserted
rather than trusted: if a revised map or a different entry ever shifts it, this
script fails instead of writing a plausible-looking but wrong CSV.
"""

import csv
import io
import pathlib
import urllib.request

import gemmi

#: Author numbering in 9GSP is a single chain running across HA1 and HA2, which
#: is the same frame as this map's ``sequential_site``.
NUMBERING_MAP_URL = (
    "https://raw.githubusercontent.com/jbloomlab/flu-seqneut-2026/main/data/"
    "nextstrain-prot-titers-tree_data/H1N1_site_numbering_map.tsv"
)

PDB_ID = "9GSP"
STRUCTURE_URL = f"https://files.rcsb.org/download/{PDB_ID}.cif"

#: The three protomers. Unlike 8FAW, 9GSP's deposited coordinates are already
#: the trimer, so every protomer needs its own rows -- there is no symmetry
#: expansion to replicate one chain's annotation onto the other two.
POLYMER_CHAINS = ("A", "B", "C")

#: Antigenic sites of H1 HA1, from Table 2 ("Amino acid sequence of antigenic
#: sites for historic H1N1 and H1N1pdm natural isolate viruses") of Wilson et
#: al., Virology 2015;485:252-62, PMC5737639. That table's footnote: "Antigenic
#: sites are based on those determined for A/PR/8/34 by Caton et al. (1982)."
#: The residue numbers themselves are those of the table's reference row,
#: A/California/07/2009, so this is Caton's set carried into the numbering of
#: the pandemic 2009 lineage rather than into A/PR/8/34's -- which is why it
#: transfers to 9GSP without an alignment step. Every residue the table shows is
#: included: unlike the H3 table it encloses none of them in parentheses.
SITES = {
    "Sa": [124, 125, 153, 154, 155, 156, 157, 159, 160, 161, 162, 163, 164],
    "Sb": [184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195],
    "Ca1": [166, 167, 168, 169, 170, 203, 204, 205, 235, 236, 237],
    "Ca2": [137, 138, 139, 140, 141, 142, 221, 222],
    "Cb": [70, 71, 72, 73, 74, 75],
}

#: The 8FAW example's colorblind-safe qualitative palette, reused in a declared
#: order. The order is deliberately not an attempt to match each H1 site to the
#: H3 site it sits nearest: Sa and Sb would then share a color, and the reader
#: would be invited to read an equivalence off the two views that the two sets
#: of definitions do not actually assert.
SITE_COLORS = {
    "Sa": "#e41a1c",
    "Sb": "#377eb8",
    "Ca1": "#4daf4a",
    "Ca2": "#984ea3",
    "Cb": "#ff7f00",
}

#: The two grays are not decoration: they draw the HA1/HA2 boundary, which is
#: what the _HA1 and _HA2 label suffixes exist to tell you about. 9GSP is an
#: uncleaved HA0, so that boundary is a position in one polypeptide rather than
#: a break between two -- and the loop across it is disordered.
HA1_COLOR = "#e8e8e8"
HA2_COLOR = "#bdbdbd"
GLYCAN_COLOR = "#ffd700"

#: Label text sits on top of a residue already painted its site color, so it
#: must not inherit that color. The size is below the 2.0 default because the
#: trimer carries every one of these labels three times.
LABEL_COLOR = "#252525"
LABEL_SIZE = "1.6"

CITATION = "Wilson et al. 2015 Virology 485:252-62"

#: Residues whose identity fixes the numbering frame, quoted in the same H1
#: numbering as the site definitions. The nine cysteines form HA1's disulfides
#: and the four aromatics line the receptor-binding site; the three HA2 entries
#: are there to pin the HA1/HA2 offset, and are quoted in author numbering like
#: the rest of this map (HA2 14, 21 and 26).
FRAME_CHECKS = {
    4: "CYS",
    42: "CYS",
    55: "CYS",
    67: "CYS",
    90: "CYS",
    98: "TYR",
    136: "CYS",
    150: "TRP",
    180: "HIS",
    192: "TYR",
    275: "CYS",
    279: "CYS",
    303: "CYS",
    341: "TRP",
    348: "TRP",
    353: "HIS",
}

#: What the numbering map has to say for the site definitions above to be usable
#: as author residue numbers: HA1 numbering *is* author numbering, and HA2 is a
#: constant offset below it. Asserting this is the only reason to fetch the map
#: rather than hard-code the offset.
HA2_OFFSET = 327

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
    """Return the 9GSP model, fetched from RCSB."""
    with urllib.request.urlopen(STRUCTURE_URL) as response:
        text = response.read().decode()
    structure = gemmi.make_structure_from_block(
        gemmi.cif.read_string(text).sole_block()
    )
    structure.setup_entities()
    return structure[0]


def partition_residues(model):
    """Split the modeled residues into polymer and glycans.

    gemmi splits waters and heteroatoms into a second chain reusing the author
    ID, so the four N-acetylglucosamines that hang off each protomer appear
    under that protomer's chain. Classify by component rather than by chain:
    amino acids on a polymer chain are the protein, and every other non-water
    residue is a glycan, whether it sits under a protomer chain or on one of the
    branched-glycan chains of its own.

    Returns two ``[(chain, residue_number, component_name), ...]`` lists.
    """
    polymer, glycans = [], []
    for chain in model:
        for residue in chain:
            info = gemmi.find_tabulated_residue(residue.name)
            if info is not None and info.is_water():
                continue
            entry = (chain.name, residue.seqid.num, residue.name)
            if (
                chain.name in POLYMER_CHAINS
                and info is not None
                and info.is_amino_acid()
            ):
                polymer.append(entry)
            else:
                glycans.append(entry)
    missing = set(POLYMER_CHAINS) - {chain for chain, _, _ in polymer}
    if missing:
        raise SystemExit(f"{PDB_ID} has no polymer on chain(s) {sorted(missing)}")
    return polymer, glycans


def check_frame(polymer):
    """Fail loudly if author numbering is not H1 numbering after all."""
    for want_chain in POLYMER_CHAINS:
        seen = {
            number: component
            for chain, number, component in polymer
            if chain == want_chain
        }
        wrong = {
            num: (expected, seen.get(num))
            for num, expected in FRAME_CHECKS.items()
            if seen.get(num) != expected
        }
        if wrong:
            raise SystemExit(
                f"{PDB_ID} chain {want_chain} is not in H1 numbering: "
                + "; ".join(
                    f"expected {exp} at {num}, found {got}"
                    for num, (exp, got) in sorted(wrong.items())
                )
            )


def check_numbering_map(numbering):
    """Fail loudly if the map no longer agrees with 9GSP's author numbering."""
    for sequential, (protein, site) in sorted(numbering.items()):
        expected = sequential if protein == "HA1" else sequential - HA2_OFFSET
        if site != expected:
            raise SystemExit(
                f"the numbering map puts sequential site {sequential} at "
                f"{site}_{protein}, not {expected}_{protein}; author numbering "
                f"in {PDB_ID} is no longer the map's own frame"
            )


def check_sites():
    """Fail loudly if the transcribed site definitions have drifted."""
    flat = [site for residues in SITES.values() for site in residues]
    if len(flat) != len(set(flat)):
        raise SystemExit("antigenic sites overlap; they are disjoint in Table 2")
    if len(flat) != 50:
        raise SystemExit(f"expected 50 antigenic-site residues, got {len(flat)}")


def site_of(residue_number):
    """Return the antigenic site containing this HA1 site, or ``None``."""
    for site, residues in SITES.items():
        if residue_number in residues:
            return site
    return None


def polymer_rows(polymer, numbering):
    """One row per modeled polymer residue, colored by antigenic site."""
    rows = []
    for chain, number, _component in polymer:
        if number not in numbering:
            raise SystemExit(
                f"{PDB_ID} chain {chain} models residue {number}, which is past "
                "the end of the numbering map"
            )
        protein, site = numbering[number]
        region = site_of(site) if protein == "HA1" else None
        # One label for every residue, antigenic site or not: the site number
        # alone is ambiguous across HA1 and HA2, and this is both the mouseover
        # text and, on an antigenic-site residue, the text drawn into the scene.
        label = f"{site}_{protein}"
        if region is not None:
            rows.append(
                [
                    chain,
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
                    chain,
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


def glycan_rows(glycans):
    """One row per N-glycan sugar, drawn in one color rather than as SNFG.

    These are not labeled: several shield an antigenic region, which is the
    point of showing them, and adding another 27 labels to a view that already
    draws 50 per protomer would obscure the thing they shield.
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
            f"N-glycan sugar ({component}); named here so it is drawn in "
            "this color rather than as an SNFG symbol",
        ]
        for chain, number, component in glycans
    ]


def main():
    check_sites()
    numbering = load_numbering_map()
    check_numbering_map(numbering)
    model = load_structure()

    polymer, glycans = partition_residues(model)
    check_frame(polymer)

    # Ordered so the file sorts by chain then residue, which is also what the
    # docs' snippet line range depends on: chain A's polymer block starts on
    # line 2 at residue 1, so HA1 residue n is on line n + 1.
    rows = sorted(
        polymer_rows(polymer, numbering) + glycan_rows(glycans),
        key=lambda row: (row[0], row[1]),
    )

    out_path = pathlib.Path(__file__).parent / "coloring.csv"
    with out_path.open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)

    labeled = sum(1 for row in rows if row[4] == "True")
    print(
        f"wrote {out_path} ({len(rows)} rows: {len(polymer)} polymer, "
        f"{len(glycans)} glycan; {labeled} with a drawn label)"
    )


if __name__ == "__main__":
    main()
