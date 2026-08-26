"""Compare the CSV residue set against the structure's addressable residue set.

Validation always runs against the **deposited** asymmetric-unit residues, so it
is independent of the assembly flag: symmetry copies never introduce new residue
numbers. Waters are excluded from the addressable set, so they never flood the
report; a CSV row that lands on a water gets its own targeted message instead of
the generic "not in structure" one.
"""

from __future__ import annotations

import dataclasses

from ._config import MISMATCH_MODES, InputError
from .residues import ColoringData, ResidueKey, keys, split_residue
from .structure import ResidueClass, addressable_residues


def sort_key(key: ResidueKey) -> tuple[str, int, str]:
    """Order residues by chain, then author number, then insertion code."""
    chain, residue = key
    number, icode = split_residue(residue)
    return (chain, number, icode)


def _format_keys(residue_keys: set[ResidueKey], limit: int | None = None) -> str:
    """Render residue keys as ``chain/residue``, optionally truncated."""
    ordered = sorted(residue_keys, key=sort_key)
    shown = ordered if limit is None else ordered[:limit]
    text = ", ".join(f"{chain}/{residue}" for chain, residue in shown)
    if limit is not None and len(ordered) > limit:
        text += f", ... ({len(ordered) - limit} more)"
    return text


@dataclasses.dataclass
class ValidationReport:
    """The three ways the CSV and the structure can disagree."""

    #: CSV rows whose ``(chain, residue)`` is not an addressable structure residue.
    in_csv_not_structure: set[ResidueKey]
    #: Addressable structure residues with no CSV row.
    in_structure_not_csv: set[ResidueKey]
    #: CSV rows present in the structure but on a chain the assembly omits.
    in_csv_not_in_assembly: set[ResidueKey]
    #: CSV rows that landed on a water. A subset of ``in_csv_not_structure``,
    #: reported with its own message rather than the generic one.
    csv_targets_water: set[ResidueKey]
    #: Class of every deposited residue, used to group ``in_structure_not_csv``.
    structure_classes: dict[ResidueKey, ResidueClass]

    def is_fatal(self, mode: str) -> bool:
        """Whether this report is fatal under an ``--on-mismatch`` mode."""
        if mode not in MISMATCH_MODES:
            raise InputError(f"unknown --on-mismatch mode {mode!r}")
        if mode == "report":
            return False
        if mode == "error-any":
            return bool(self.in_csv_not_structure or self.in_structure_not_csv)
        if mode == "error-extra-in-pdb":
            return bool(self.in_structure_not_csv)
        return bool(self.in_csv_not_structure)  # error-extra-in-csv

    def format(self) -> str:
        """The mismatch report, grouped by direction."""
        lines = ["Mismatch report", "==============="]

        lines.append("")
        lines.append(
            f"Residues in CSV but not in structure: {len(self.in_csv_not_structure)}"
        )
        non_water = self.in_csv_not_structure - self.csv_targets_water
        if non_water:
            lines.append(f"  no such residue: {_format_keys(non_water)}")
        for chain, residue in sorted(self.csv_targets_water, key=sort_key):
            lines.append(
                f"  {chain}/{residue} targets a water residue; waters are not "
                "individually addressable, use --waters"
            )

        lines.append("")
        lines.append(
            f"Residues in structure but not in CSV: {len(self.in_structure_not_csv)}"
        )
        by_class: dict[ResidueClass, set[ResidueKey]] = {}
        for key in self.in_structure_not_csv:
            by_class.setdefault(self.structure_classes[key], set()).add(key)
        for residue_class in ("polymer", "ligand", "glycan", "ion"):
            group = by_class.get(residue_class)
            if group:
                lines.append(
                    f"  {residue_class} ({len(group)}): {_format_keys(group, limit=20)}"
                )

        lines.append("")
        lines.append(
            "Residues in CSV and structure but absent from the chosen assembly: "
            f"{len(self.in_csv_not_in_assembly)}"
        )
        if self.in_csv_not_in_assembly:
            lines.append(f"  {_format_keys(self.in_csv_not_in_assembly)}")

        return "\n".join(lines)


def validate(
    coloring: ColoringData,
    deposited: dict[ResidueKey, ResidueClass],
    assembly_chains: set[str] | None,
    mode: str,
) -> ValidationReport:
    """Compare CSV keys against the deposited residues.

    All three mismatch sets are always computed;
    `ValidationReport.is_fatal` is what applies the mode.

    Parameters
    ----------
    coloring
        The parsed CSV.
    deposited
        Deposited residues and their classes, from
        `prot_struct_viz.structure.get_deposited_residues`.
    assembly_chains
        Chains used by the chosen assembly, or ``None`` for the asymmetric unit.
    mode
        One of `prot_struct_viz._config.MISMATCH_MODES`. Validated here so
        a bad mode fails before any work is done.

    Returns
    -------
    ValidationReport
    """
    if mode not in MISMATCH_MODES:
        raise InputError(
            f"--on-mismatch must be one of {list(MISMATCH_MODES)}, got {mode!r}"
        )

    csv_keys = keys(coloring)
    addressable = addressable_residues(deposited)

    in_csv_not_structure = csv_keys - addressable
    csv_targets_water = {
        key for key in in_csv_not_structure if deposited.get(key) == "water"
    }

    in_structure_not_csv = addressable - csv_keys

    if assembly_chains is None:
        in_csv_not_in_assembly: set[ResidueKey] = set()
    else:
        in_csv_not_in_assembly = {
            key for key in csv_keys & addressable if key[0] not in assembly_chains
        }

    return ValidationReport(
        in_csv_not_structure=in_csv_not_structure,
        in_structure_not_csv=in_structure_not_csv,
        in_csv_not_in_assembly=in_csv_not_in_assembly,
        csv_targets_water=csv_targets_water,
        structure_classes=dict(deposited),
    )
