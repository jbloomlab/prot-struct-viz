"""Defaults, allowed values, and the error type raised on bad user input.

Every set of allowed values a user can name lives here and is imported by the
parser and the renderer, so there is one place to look for what an option will
accept. What each option *means* is written once, in ``docs/spec.md``;
`prot_struct_viz.spec.OPTION_KEYS` is the list of their names.
"""

from __future__ import annotations

import dataclasses
import re

from ._colors import CSS_COLORS

#: Default color for structure residues that have no CSV row.
DEFAULT_COLOR = "#d9d9d9"

#: Representation applied to the whole displayed polymer unless overridden.
DEFAULT_REPRESENTATION = "cartoon"

#: Height of the viewer box when the spec does not give one, as a CSS length.
DEFAULT_VIEWER_HEIGHT = "70vh"

#: Whether Mol*'s own panels start open when the spec does not say.
DEFAULT_MOLSTAR_UI = "show"

#: Whether Mol*'s own panels start open or closed.
MOLSTAR_UI_MODES = ("show", "hide")

#: Rendering look applied to the whole page when the spec does not say.
DEFAULT_STYLE = "default"

#: Rendering looks a page may ask for. ``illustrative`` is Mol*'s own flat-shaded,
#: outlined, ambient-occluded look; ``default`` is Mol*'s untouched rendering.
#: Neither changes a color: every color on the page comes from the CSV.
STYLES = ("default", "illustrative")

#: Allowed values for each heteroatom flag. Glycans take ``snfg`` rather than
#: ``show`` because showing one means drawing it as a 3D-SNFG symbol.
HETERO_FLAG_CHOICES = {
    "waters": ("show", "hide"),
    "ligands": ("show", "hide"),
    "glycans": ("snfg", "hide"),
    "ions": ("show", "hide"),
}

#: What to do when the CSV and the structure disagree about the residue set.
MISMATCH_MODES = (
    "error-any",
    "error-extra-in-pdb",
    "error-extra-in-csv",
    "report",
)

#: Representations a user may name, mapped to the keyword arguments the MolViewSpec
#: builder's ``representation()`` is called with. This is the single source of
#: allowed values for the CSV ``representation`` column, ``default_representation``,
#: and ``chain_representation``.
#:
#: The value is kwargs rather than a type string because a token may name a
#: *parameterized* representation: Gaussian is not a type of its own in
#: MolViewSpec but a ``surface_type`` of the surface representation. The token is
#: also what identifies a representation everywhere else in this package, so two
#: tokens differing only in a parameter stay distinguishable.
#:
#: Mol* itself also draws ``backbone``, ``line``, and ``putty``, but the
#: molviewspec Python package we build the state with does not accept them yet,
#: so naming one would produce a state that fails validation. They are left out
#: rather than offered and silently broken.
REPRESENTATIONS = {
    "cartoon": {"type": "cartoon"},
    "ball-and-stick": {"type": "ball_and_stick"},
    "spacefill": {"type": "spacefill"},
    "surface": {"type": "surface"},
    "gaussian-surface": {"type": "surface", "surface_type": "gaussian"},
    "carbohydrate": {"type": "carbohydrate"},
}

#: Color of persistent on-structure label text when the CSV does not give one.
DEFAULT_LABEL_COLOR = "#000000"

#: Height of persistent label text, in Angstroms of world space, when the CSV does
#: not give one. Mol*'s own default of 1 is about a bond length and reads very small
#: beside a residue.
DEFAULT_LABEL_SIZE = 2.0

#: Representation given to a CSV-named non-polymer residue that does not specify
#: one of its own. The global/per-chain base is a polymer representation
#: (``cartoon`` by default) and would draw nothing for a ligand or ion.
HETERO_CSV_REPRESENTATION = "ball-and-stick"


class InputError(Exception):
    """Raised on invalid user input (bad CSV, bad structure, failed validation).

    The CLI catches this, writes the report, and exits non-zero. It never
    carries a traceback to the user: the message is the whole story.
    """


_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def normalize_color(value: str) -> str:
    """Normalize a hex or CSS/X11 named color to lowercase ``#rrggbb``.

    Every color the user can give -- the CSV's ``color`` and ``label_color``
    columns and the spec's ``default_color`` -- comes through here, so an invalid
    color fails at the boundary rather than reaching Mol* as a string it silently
    ignores.

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


@dataclasses.dataclass(frozen=True)
class ViewConfig:
    """Everything that controls a rendered view, shared by the CLI and ``render``.

    Field names are spec-file keys; what each one means is in ``docs/spec.md``.
    """

    assembly: str = "au"
    chains: tuple[str, ...] | None = None
    on_mismatch: str = "report"
    default_color: str = DEFAULT_COLOR
    default_representation: str = DEFAULT_REPRESENTATION
    waters: str = "hide"
    ligands: str = "show"
    glycans: str = "snfg"
    ions: str = "show"

    def __post_init__(self):
        if self.on_mismatch not in MISMATCH_MODES:
            raise InputError(
                f"on_mismatch must be one of {list(MISMATCH_MODES)}, got "
                f"{self.on_mismatch!r}"
            )
        for name, allowed in HETERO_FLAG_CHOICES.items():
            value = getattr(self, name)
            if value not in allowed:
                raise InputError(
                    f"{name} must be one of {list(allowed)}, got {value!r}"
                )
        if self.default_representation not in REPRESENTATIONS:
            raise InputError(
                f"default_representation must be one of {sorted(REPRESENTATIONS)}, "
                f"got {self.default_representation!r}"
            )
        if not isinstance(self.default_color, str):
            raise InputError(
                f"default_color must be a color, got "
                f"{type(self.default_color).__name__}"
            )
        # Normalized rather than merely checked, so that every color reaching the
        # MVS state is #rrggbb whether it came from the spec or from a CSV cell.
        try:
            normalized = normalize_color(self.default_color)
        except InputError as err:
            raise InputError(f"default_color: {err}") from None
        object.__setattr__(self, "default_color", normalized)
