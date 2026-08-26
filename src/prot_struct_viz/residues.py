"""Parse and validate the residue CSV that drives colors, labels, and styling.

Parsing is strict: a missing required column, a blank required cell, an invalid
color, an unparseable residue number, an unknown representation, or a duplicated
``(chain, residue)`` key is a fatal error naming the offending line and column.
Defaults are never substituted for a required cell. The one display default
(`prot_struct_viz._config.DEFAULT_COLOR`) applies to structure residues
with no CSV row at all, which is a rendering choice, not a parsing one.
"""

from __future__ import annotations

import csv
import dataclasses
import pathlib
import re

import pandas as pd

from ._colors import CSS_COLORS
from ._config import REPRESENTATIONS, InputError

#: ``(chain, residue)``, where residue is a string carrying any insertion code.
ResidueKey = tuple[str, str]

#: An author residue number with an optional single-letter insertion code.
RESIDUE_RE = re.compile(r"^(-?\d+)([A-Za-z]?)$")

_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

#: Name of the single scheme when the CSV has a bare ``color`` column.
DEFAULT_SCHEME = "Default"


@dataclasses.dataclass(frozen=True)
class ResidueSpec:
    """One CSV row: what to do with one deposited residue."""

    chain: str
    residue: str
    colors: dict[str, str]
    label: str | None
    show_label: bool
    representation: str | None
    label_color: str | None
    label_size: float | None

    @property
    def key(self) -> ResidueKey:
        return (self.chain, self.residue)


@dataclasses.dataclass(frozen=True)
class ColoringData:
    """The parsed CSV: one spec per row, plus the color schemes it defines."""

    specs: list[ResidueSpec]
    scheme_names: list[str]


def normalize_color(value: str) -> str:
    """Normalize a hex or CSS/X11 named color to lowercase ``#rrggbb``.

    Parameters
    ----------
    value
        A hex color (``#abc`` or ``#aabbcc``) or a CSS color name (``red``).

    Returns
    -------
    str
        The color as ``#rrggbb``.

    Raises
    ------
    InputError
        If the value is not a recognized color.
    """
    text = value.strip()
    if _HEX_RE.match(text):
        digits = text[1:].lower()
        if len(digits) == 3:
            digits = "".join(c * 2 for c in digits)
        return f"#{digits}"
    named = CSS_COLORS.get(text.lower())
    if named is not None:
        return named
    raise InputError(
        f"{value!r} is not a valid color: use hex (#1f77b4) or a CSS color name (red)"
    )


def split_residue(residue: str) -> tuple[int, str]:
    """Split a residue string into its author number and insertion code.

    ``"52"`` -> ``(52, "")`` and ``"52A"`` -> ``(52, "A")``.
    """
    match = RESIDUE_RE.match(residue)
    if match is None:
        raise InputError(
            f"{residue!r} is not an author residue number with an optional "
            "insertion code (e.g. '52' or '52A')"
        )
    return int(match.group(1)), match.group(2)


def keys(coloring: ColoringData) -> set[ResidueKey]:
    """The set of ``(chain, residue)`` keys named by the CSV."""
    return {spec.key for spec in coloring.specs}


def _read_header(path: pathlib.Path) -> list[str]:
    """The raw header row, so duplicate column names can be caught."""
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            return [cell.strip() for cell in row]
    raise InputError(f"{path} is empty")


def _read_table(path: pathlib.Path) -> pd.DataFrame:
    """Read a CSV with every cell a string and blanks as ``""``.

    Reading as strings is what keeps residue numbers from being coerced to
    integers, which would silently drop insertion codes.
    """
    if not path.is_file():
        raise InputError(f"no such file: {path}")
    header = _read_header(path)
    duplicated = sorted({c for c in header if header.count(c) > 1})
    if duplicated:
        raise InputError(f"{path}: duplicate column name(s): {duplicated}")
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    frame.columns = [str(c).strip() for c in frame.columns]
    return frame


def _color_columns(columns: list[str], path: pathlib.Path) -> dict[str, str]:
    """Map scheme name -> column name, from ``color`` or ``color:<Scheme>`` columns."""
    bare = [c for c in columns if c == "color"]
    scheme_cols = [c for c in columns if c.startswith("color:")]
    if bare and scheme_cols:
        raise InputError(
            f"{path}: has both a bare 'color' column and {scheme_cols}; use one or "
            "the other, not both"
        )
    if bare:
        return {DEFAULT_SCHEME: "color"}
    if not scheme_cols:
        raise InputError(
            f"{path}: missing required column 'color' (or at least one "
            "'color:<SchemeName>' column)"
        )
    schemes = {}
    for column in scheme_cols:
        name = column.split(":", 1)[1].strip()
        if not name:
            raise InputError(f"{path}: column {column!r} has an empty scheme name")
        if name in schemes:
            raise InputError(
                f"{path}: scheme {name!r} is defined by more than one column"
            )
        schemes[name] = column
    return schemes


def _parse_bool(value: str, line: int) -> bool:
    """Parse a ``show_label`` cell; empty means False."""
    text = value.strip().lower()
    if text == "":
        return False
    if text in ("true", "false"):
        return text == "true"
    raise InputError(
        f"line {line}, column 'show_label': {value!r} is not a boolean; use "
        "'True' or 'False' (or leave it empty)"
    )


def _parse_label_size(value: str, line: int) -> float | None:
    """Parse a ``label_size`` cell; empty means "use the default"."""
    text = value.strip()
    if text == "":
        return None
    try:
        size = float(text)
    except ValueError:
        raise InputError(
            f"line {line}, column 'label_size': {value!r} is not a number; label "
            "size is the text height in Angstroms (e.g. 2)"
        ) from None
    if size <= 0:
        raise InputError(f"line {line}, column 'label_size': {value!r} is not positive")
    return size


def parse_csv(path: pathlib.Path) -> ColoringData:
    """Parse and validate the residue CSV.

    Parameters
    ----------
    path
        Path to the CSV. Required columns are ``chain``, ``residue``, and
        ``color`` (or one or more ``color:<SchemeName>`` columns). Optional
        columns are ``label``, ``show_label``, ``representation``,
        ``label_color``, and ``label_size``. Any other columns are ignored.

        ``label_color`` and ``label_size`` style the persistent on-structure
        label, so they do nothing on a row whose ``show_label`` is not true. That
        is deliberately not an error: it lets a colour be set on every row while
        ``show_label`` is toggled during figure iteration.

    Returns
    -------
    ColoringData
        One `ResidueSpec` per row, and the scheme names in column order.

    Raises
    ------
    InputError
        On any missing column, blank required cell, or invalid value. All
        offending lines are reported together rather than one at a time.
    """
    path = pathlib.Path(path)
    frame = _read_table(path)

    missing = [c for c in ("chain", "residue") if c not in frame.columns]
    if missing:
        raise InputError(f"{path}: missing required column(s): {missing}")
    schemes = _color_columns(list(frame.columns), path)

    problems: list[str] = []
    specs: list[ResidueSpec] = []
    seen: dict[ResidueKey, int] = {}

    for offset, row in enumerate(frame.to_dict("records")):
        line = offset + 2  # +1 for the header, +1 for 1-based line numbers
        row_problems: list[str] = []

        chain = str(row["chain"]).strip()
        residue = str(row["residue"]).strip()
        for name, value in (("chain", chain), ("residue", residue)):
            if value == "":
                row_problems.append(
                    f"line {line}, column {name!r}: required value is blank"
                )

        if residue != "":
            try:
                split_residue(residue)
            except InputError as err:
                row_problems.append(f"line {line}, column 'residue': {err}")

        colors = {}
        for scheme, column in schemes.items():
            raw = str(row[column]).strip()
            if raw == "":
                row_problems.append(
                    f"line {line}, column {column!r}: required value is blank"
                )
                continue
            try:
                colors[scheme] = normalize_color(raw)
            except InputError as err:
                row_problems.append(f"line {line}, column {column!r}: {err}")

        label = str(row.get("label", "")).strip() or None

        try:
            show_label = _parse_bool(str(row.get("show_label", "")), line)
        except InputError as err:
            row_problems.append(str(err))
            show_label = False
        if show_label and label is None:
            row_problems.append(
                f"line {line}: show_label is True but 'label' is empty; a "
                "persistent label needs text to draw"
            )

        representation = str(row.get("representation", "")).strip() or None
        if representation is not None and representation not in REPRESENTATIONS:
            row_problems.append(
                f"line {line}, column 'representation': {representation!r} is not "
                f"one of {sorted(REPRESENTATIONS)}"
            )
            representation = None

        label_color = str(row.get("label_color", "")).strip() or None
        if label_color is not None:
            try:
                label_color = normalize_color(label_color)
            except InputError as err:
                row_problems.append(f"line {line}, column 'label_color': {err}")
                label_color = None

        try:
            label_size = _parse_label_size(str(row.get("label_size", "")), line)
        except InputError as err:
            row_problems.append(str(err))
            label_size = None

        if not row_problems:
            key = (chain, residue)
            if key in seen:
                problems.append(
                    f"line {line}: duplicate entry for chain {chain!r} residue "
                    f"{residue!r} (first seen on line {seen[key]})"
                )
                continue
            seen[key] = line
            specs.append(
                ResidueSpec(
                    chain=chain,
                    residue=residue,
                    colors=colors,
                    label=label,
                    show_label=show_label,
                    representation=representation,
                    label_color=label_color,
                    label_size=label_size,
                )
            )
        problems.extend(row_problems)

    if problems:
        raise InputError(f"{path} is invalid:\n  " + "\n  ".join(problems))
    if not specs:
        raise InputError(f"{path}: has no data rows")

    return ColoringData(specs=specs, scheme_names=list(schemes))


def parse_chain_representations(path: pathlib.Path) -> dict[str, str]:
    """Parse the optional ``chain,representation`` override file.

    Returns
    -------
    dict
        Chain ID -> representation token from
        `prot_struct_viz._config.REPRESENTATIONS`.
    """
    path = pathlib.Path(path)
    frame = _read_table(path)
    missing = [c for c in ("chain", "representation") if c not in frame.columns]
    if missing:
        raise InputError(f"{path}: missing required column(s): {missing}")

    problems: list[str] = []
    overrides: dict[str, str] = {}
    for offset, row in enumerate(frame.to_dict("records")):
        line = offset + 2
        chain = str(row["chain"]).strip()
        representation = str(row["representation"]).strip()
        if chain == "":
            problems.append(f"line {line}, column 'chain': required value is blank")
            continue
        if representation not in REPRESENTATIONS:
            problems.append(
                f"line {line}, column 'representation': {representation!r} is not "
                f"one of {sorted(REPRESENTATIONS)}"
            )
            continue
        if chain in overrides:
            problems.append(f"line {line}: duplicate entry for chain {chain!r}")
            continue
        overrides[chain] = representation

    if problems:
        raise InputError(f"{path} is invalid:\n  " + "\n  ".join(problems))
    return overrides
