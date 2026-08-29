"""Regenerate the five coloring CSVs for the 9GSP antigenic-regions example.

The CSVs are committed, and this script is **not** run by
``scripts/build_examples.sh`` or by the tests -- ``spec.yaml`` reads the
committed files. Run this by hand when the inputs below change::

    .venv/bin/python examples/9gsp_antigenic_regions/make_coloring_csv.py

This is the H1 counterpart of the 8FAW script next door, and follows it view for
view; the differences are all consequences of the entry. 9GSP deposits the whole
trimer rather than one protomer, so every annotation covers three chains instead
of relying on symmetry, and nothing is bound to the receptor site.

It writes one CSV per view of ``spec.yaml``, each named after the view that
reads it -- so a name here that no view claims is a name that has gone stale:

* ``antigenic-regions-w-glycans.csv`` -- every modeled residue, HA1 colored by
  antigenic region, plus the N-glycans;
* ``antigenic-regions.csv`` -- the same without the glycan rows, so that the
  view's ``glycans: hide`` can take them away;
* ``california-2009-to-d-3-1.csv`` and ``d-3-1-to-d-3-1-1.csv`` -- the sites that
  differ between two HAs, in red;
* ``d-3-1-1-with-g155e.csv`` -- the second of those two lists again, with HA1 155
  added in the color its own antigenic region already has.

Two things it fetches rather than hard-codes:

* the lab's H1N1 site-numbering map, which is what splits a residue number into
  an HA1 or HA2 site number;
* PDB 9GSP itself, so that only *modeled* residues get a row.

The two mutation lists are the exception: they are hard-coded below rather than
recomputed from the sequence libraries they came from, so that this repository
depends on nothing outside itself. What the script still owns for them is the
mapping from an HA1/HA2 site to a residue of 9GSP, and the check that every one
of them is actually modeled.

The numbering frame is the load-bearing assumption throughout, so it is asserted
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
#: expansion to replicate one chain's annotation onto the other two. That is
#: true of the mutation views as well as the antigenic-site ones.
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
# Paul Tol's "muted" scheme, cool subset. Every one of these is cool, so on the
# structure warm means "changed or added" -- the red of a mutated site, the gold
# of a glycan -- and nothing else is close to MUTATED_COLOR. The assignment keeps
# green and purple on the sites that already had them, so only the colors that
# had to move got new names.
SITE_COLORS = {
    "Sa": "#332288",
    "Sb": "#88CCEE",
    "Ca1": "#117733",
    "Ca2": "#AA4499",
    "Cb": "#44AA99",
}

#: The two grays are not decoration: they draw the HA1/HA2 boundary, which is
#: what the _HA1 and _HA2 label suffixes exist to tell you about. 9GSP is an
#: uncleaved HA0, so that boundary is a position in one polypeptide rather than
#: a break between two -- and the loop across it is disordered.
HA1_COLOR = "#e8e8e8"
HA2_COLOR = "#bdbdbd"
GLYCAN_COLOR = "#ffd700"

#: Sites that differ between the two HAs of a comparison. Deliberately the same
#: red the 8FAW example uses, and warm where every `SITE_COLORS` entry is cool:
#: the last three views drop the antigenic-region coloring, and the one of them
#: that puts a region color back has to hold it apart from this.
MUTATED_COLOR = "#e41a1c"

#: HA1 155, drawn on top of a mutation list in the last view. G155E is a real
#: mutation on the D.3.1.1 background -- the 2026 library carries a
#: ``D.3.1.1:G155E`` strain whose only difference from the plain D.3.1.1 strain
#: is there -- and the site is one of the thirteen `SITES` assigns to
#: antigenic region Sa.
SA_SITE = 155

#: The indigo the first two views already give antigenic region Sa, so the residue
#: reads as the same thing here as it does there. That is the whole reason this
#: is not a new color: the other views' key is the key for this one too. It is
#: also a cool color against `MUTATED_COLOR`, which is the other requirement --
#: this is the only view drawing two colored classes of site at once.
SA_COLOR = SITE_COLORS["Sa"]

CITATION = "Wilson et al. 2015 Virology 485:252-62"

#: How each HA is named in a tooltip and in the CSV's ``notes`` column, with the
#: GenBank accession of the sequence actually compared.
CALIFORNIA = "A/California/07/2009 (FJ966974)"
D31 = "subclade D.3.1 (A/Missouri/11/2025, PV886191)"
D311 = "subclade D.3.1.1 (A/Andalucia/PMC-00977/2025, PX399795)"

#: Sites differing between two HAs, as ``(protein, site, from, to)``.
#:
#: Both lists were computed once from the three HA ectodomain protein sequences
#: named above -- as they appear in the Bloom lab's sequencing libraries, which
#: is why each is pinned to an accession here -- and then transcribed. The 2009
#: sequence comes from the flu-seqneut-cellular-therapy library; each subclade is
#: represented by the one strain the 2026 library assigns that subclade as its
#: whole ``derived_haplotype``, which is the same rule the 8FAW example used to
#: pick subclade K.
#:
#: All three ectodomains are 500 residues with no indels, so they compare
#: position by position with no alignment -- but unlike the H3 libraries, these
#: start at HA1 site 4 rather than site 1. flu-seqneut-2026's ``config.yml`` says
#: so where it builds its alignment: ``H1N1: DTL  # add these three amino acids
#: as HAs in viral barcode miss first 3 ectodomain aas``. So ectodomain position
#: p is HA1 site p + 3 up to p = 324, and HA2 site p - 324 after that -- which
#: leaves HA1 1-3 outside the comparison even though 9GSP models them.
#:
#: Substitutions outside what 9GSP models are dropped rather than listed: the
#: 2009 comparison's ``HA2 E172K`` falls past the last modeled residue.
CAL_TO_D31 = [
    ("HA1", 54, "K", "Q"),
    ("HA1", 74, "S", "R"),
    ("HA1", 83, "P", "S"),
    ("HA1", 84, "S", "N"),
    ("HA1", 97, "D", "N"),
    ("HA1", 120, "T", "A"),
    ("HA1", 129, "N", "D"),
    ("HA1", 130, "K", "N"),
    ("HA1", 137, "P", "S"),
    ("HA1", 142, "K", "R"),
    ("HA1", 156, "N", "K"),
    ("HA1", 161, "L", "I"),
    ("HA1", 162, "S", "N"),
    ("HA1", 163, "K", "Q"),
    ("HA1", 164, "S", "T"),
    ("HA1", 183, "S", "P"),
    ("HA1", 185, "S", "I"),
    ("HA1", 186, "A", "T"),
    ("HA1", 189, "Q", "E"),
    ("HA1", 203, "S", "T"),
    ("HA1", 216, "I", "A"),
    ("HA1", 224, "E", "A"),
    ("HA1", 250, "V", "A"),
    ("HA1", 256, "A", "T"),
    ("HA1", 259, "R", "K"),
    ("HA1", 260, "N", "E"),
    ("HA1", 277, "T", "A"),
    ("HA1", 283, "K", "E"),
    ("HA1", 295, "I", "V"),
    ("HA1", 308, "K", "R"),
    ("HA1", 321, "I", "V"),
    ("HA2", 29, "E", "D"),
    ("HA2", 45, "I", "V"),
    ("HA2", 47, "E", "K"),
    ("HA2", 91, "I", "V"),
    ("HA2", 124, "S", "H"),
    ("HA2", 133, "I", "T"),
]

D31_TO_D311 = [
    ("HA1", 113, "R", "K"),
    ("HA1", 139, "A", "D"),
    ("HA1", 283, "E", "K"),
    ("HA1", 302, "K", "E"),
]

#: Expected lengths of the two lists above, asserted for the same reason
#: `check_sites` asserts the antigenic sites' size: a hand-transcribed list is
#: worth nothing if a dropped line goes unnoticed.
MUTATION_COUNTS = {"CAL_TO_D31": 37, "D31_TO_D311": 4}

HEADER = [
    "chain",
    "residue",
    "color",
    "label",
    "representation",
    "notes",
]

#: What the numbering map has to say for the site definitions above to be usable
#: as author residue numbers: HA1 numbering *is* author numbering, and HA2 is a
#: constant offset below it. Asserting this is the only reason to fetch the map
#: rather than hard-code the offset.
HA2_OFFSET = 327

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


def site_of(residue_number_):
    """Return the antigenic site containing this HA1 site, or ``None``."""
    for site, residues in SITES.items():
        if residue_number_ in residues:
            return site
    return None


def residue_number(protein, site):
    """Return the 9GSP author residue number of an HA1 or HA2 site."""
    if protein == "HA1":
        return site
    if protein == "HA2":
        return site + HA2_OFFSET
    raise SystemExit(f"unknown protein {protein!r}; expected 'HA1' or 'HA2'")


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
        # alone is ambiguous across HA1 and HA2, and this is the mouseover text.
        label = f"{site}_{protein}"
        if region is not None:
            rows.append(
                [
                    chain,
                    number,
                    SITE_COLORS[region],
                    label,
                    "",
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
                    f"{protein} site {site}; not in a defined antigenic site",
                ]
            )
    return rows


def glycan_rows(glycans):
    """One row per N-glycan sugar, drawn in one color rather than as SNFG.

    Only the first view's CSV gets these. Leaving them out of the other four is
    what lets those views' ``glycans: hide`` take them away, since a residue
    named in the CSV is drawn whatever the heteroatom options say.
    """
    return [
        [
            chain,
            number,
            GLYCAN_COLOR,
            component,
            "ball-and-stick",
            f"N-glycan sugar ({component}); named here so it is drawn in "
            "this color rather than as an SNFG symbol",
        ]
        for chain, number, component in glycans
    ]


def check_mutations(name, mutations, modeled):
    """Fail loudly if a hard-coded mutation list has drifted or gone unmodeled.

    Both failures would otherwise be silent: a dropped line just loses a red
    site, and a site 9GSP does not model would be reported by ``on_mismatch``
    but only as one line among the rest of the build's output.
    """
    expected = MUTATION_COUNTS[name]
    if len(mutations) != expected:
        raise SystemExit(f"{name} has {len(mutations)} entries, expected {expected}")
    seen = {(protein, site) for protein, site, _, _ in mutations}
    if len(seen) != len(mutations):
        raise SystemExit(f"{name} names the same site twice")
    absent = [
        f"{site}_{protein}"
        for protein, site, _, _ in mutations
        if residue_number(protein, site) not in modeled
    ]
    if absent:
        raise SystemExit(f"{name} names sites {PDB_ID} does not model: {absent}")


def mutation_rows(mutations, from_name, to_name):
    """Red rows for the differing sites, on every protomer.

    The antigenic-site coloring is gone from these views: every residue without
    a row here takes the view's ``default_color``, so the only thing painted is
    what changed. The tooltip carries the substitution itself, which is the only
    way to read the view -- no label is drawn into the scene.
    """
    return [
        [
            chain,
            residue_number(protein, site),
            MUTATED_COLOR,
            f"{old}{site}{new}_{protein}",
            "",
            f"{protein} site {site} differs: {old} in {from_name}, "
            f"{new} in {to_name}",
        ]
        for chain in POLYMER_CHAINS
        for protein, site, old, new in mutations
    ]


def sa_site_rows(mutations, modeled):
    """A row per protomer for `SA_SITE`, for the view that adds it.

    These are written alongside `mutation_rows` into a single CSV, so all three
    of the things that could make that CSV lie are checked here: that the site
    really is in antigenic region Sa, that 9GSP models it, and that the mutation
    list does not already claim it -- two rows for one residue would leave the
    file saying nothing about which color wins.
    """
    if SA_SITE not in SITES["Sa"]:
        raise SystemExit(f"HA1 site {SA_SITE} is not in antigenic region Sa")
    if residue_number("HA1", SA_SITE) not in modeled:
        raise SystemExit(f"{PDB_ID} does not model HA1 site {SA_SITE}")
    if ("HA1", SA_SITE) in {(protein, site) for protein, site, _, _ in mutations}:
        raise SystemExit(f"HA1 site {SA_SITE} is painted by the mutation list already")
    return [
        [
            chain,
            residue_number("HA1", SA_SITE),
            SA_COLOR,
            f"{SA_SITE}_HA1",
            "",
            f"HA1 site {SA_SITE}; antigenic region Sa of {CITATION}, and the site "
            "of G155E on the D.3.1.1 background",
        ]
        for chain in POLYMER_CHAINS
    ]


def write_csv(name, rows, note):
    """Write one CSV beside this script and say what went into it."""
    out_path = pathlib.Path(__file__).parent / name
    with out_path.open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)
    print(f"wrote {out_path} ({len(rows)} rows: {note})")


def main():
    check_sites()
    numbering = load_numbering_map()
    check_numbering_map(numbering)
    model = load_structure()

    polymer, glycans = partition_residues(model)
    check_frame(polymer)
    modeled = {number for _, number, _ in polymer}
    check_mutations("CAL_TO_D31", CAL_TO_D31, modeled)
    check_mutations("D31_TO_D311", D31_TO_D311, modeled)

    # Every CSV is sorted by chain then residue, so a reader can find a residue
    # in it the same way in all five.
    def by_position(rows):
        return sorted(rows, key=lambda row: (row[0], row[1]))

    protein = by_position(polymer_rows(polymer, numbering))
    sugars = by_position(glycan_rows(glycans))

    write_csv(
        "antigenic-regions-w-glycans.csv",
        by_position(protein + sugars),
        f"{len(protein)} polymer, {len(sugars)} glycan",
    )
    write_csv(
        "antigenic-regions.csv",
        protein,
        f"{len(protein)} polymer; glycans left out so the view's "
        "`glycans: hide` can take them away",
    )
    write_csv(
        "california-2009-to-d-3-1.csv",
        by_position(mutation_rows(CAL_TO_D31, CALIFORNIA, D31)),
        f"{len(CAL_TO_D31)} differing sites on each of "
        f"{len(POLYMER_CHAINS)} protomers",
    )
    subclade = mutation_rows(D31_TO_D311, D31, D311)
    write_csv(
        "d-3-1-to-d-3-1-1.csv",
        by_position(subclade),
        f"{len(D31_TO_D311)} differing sites on each of "
        f"{len(POLYMER_CHAINS)} protomers",
    )
    write_csv(
        "d-3-1-1-with-g155e.csv",
        by_position(subclade + sa_site_rows(D31_TO_D311, modeled)),
        f"{len(D31_TO_D311)} differing sites and HA1 {SA_SITE} on each of "
        f"{len(POLYMER_CHAINS)} protomers",
    )


if __name__ == "__main__":
    main()
