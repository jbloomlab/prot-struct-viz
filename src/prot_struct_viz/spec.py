"""The YAML spec file: the whole input to a render.

One file describes one output page. Keys shared by every view sit at the top
level; the ``views`` list holds one mapping per view, and a view is exactly a
name, a CSV, and a `prot_struct_viz.ViewConfig`.

**The loader supplies no defaults for per-view keys.** A view either states what
it wants or the file is rejected, so a spec can be read on its own without
knowing what this package would have filled in. Repetition across views is the
author's to remove, with YAML anchors -- which is what the reserved top-level
``definitions`` key is for: the loader ignores it, and it gives anchors somewhere
to live.

The exception is keys whose absence is itself the answer. ``chains`` omitted
means every chain, ``title_md`` omitted means no caption, ``chain_representation``
omitted means no per-chain overrides. There is nothing for the author to say.

Key names are the field names of `prot_struct_viz.ViewConfig` and the keys of
`prot_struct_viz._config.OPTION_DOCS`, so the spec file, the Python API, and the
docs cannot drift apart about what an option means.
"""

from __future__ import annotations

import dataclasses
import pathlib
import re

import yaml

from ._config import InputError, ViewConfig

#: Top-level keys every spec must give.
SHARED_KEYS = ("structure", "out", "assembly", "on_mismatch")

#: Top-level keys that may be omitted. These describe the page rather than the
#: view -- how tall the viewport is, whether Mol*'s own panels start open -- and
#: they default to what the package did before they existed, so adding one to the
#: format does not invalidate a spec written without it. The no-defaults rule is
#: about *views*: a view has to describe itself, because that is what makes a spec
#: readable on its own.
OPTIONAL_SHARED_KEYS = ("viewer_height", "molstar_ui")

#: Lengths the viewer height may be given in. Anything else is a typo, and a typo
#: here collapses the viewport silently in the browser rather than failing here.
_CSS_LENGTH = re.compile(r"^\d+(\.\d+)?(px|rem|em|vh|%)$")

#: Top-level key holding YAML anchor targets. Ignored entirely: it exists so a
#: spec can define an anchor without smuggling in a view or a default.
DEFINITIONS_KEY = "definitions"

#: Per-view keys that must be given. Every one of them would otherwise need a
#: default, and defaults are what this format is avoiding.
REQUIRED_VIEW_KEYS = (
    "name",
    "csv",
    "default_color",
    "default_representation",
    "waters",
    "ligands",
    "glycans",
    "ions",
)

#: Per-view keys that may be omitted, because omitting one says something: no
#: chain filter, no per-chain overrides, no caption, and -- for ``orientation`` --
#: leave the camera wherever the reader put it.
OPTIONAL_VIEW_KEYS = ("chains", "chain_representation", "title_md", "orientation")

#: Keys of an ``orientation`` block. ``position`` and ``target`` define the view;
#: ``up`` and ``radius`` have sensible fallbacks, so a hand-written orientation can
#: give just the two that matter.
ORIENTATION_KEYS = ("position", "target", "up", "radius")


@dataclasses.dataclass(frozen=True)
class Orientation:
    """Where the camera sits for one view.

    A subset of Mol*'s camera snapshot: the page hands this to
    ``managers.camera.setSnapshot``, which fills in the rest from the scene. That
    is why there is no ``radiusMax`` or clipping here -- those belong to the scene,
    not to a spec file, and pinning them would only make a view clip oddly on a
    structure of a different size.
    """

    position: tuple[float, float, float]
    target: tuple[float, float, float]
    up: tuple[float, float, float] = (0.0, 1.0, 0.0)
    radius: float | None = None

    def as_dict(self) -> dict:
        """JSON-able form, for embedding in the page."""
        snapshot = {
            "position": list(self.position),
            "target": list(self.target),
            "up": list(self.up),
        }
        if self.radius is not None:
            snapshot["radius"] = self.radius
        return snapshot


@dataclasses.dataclass(frozen=True)
class View:
    """One named view of the structure: what to draw and how to draw it."""

    name: str
    csv: pathlib.Path
    config: ViewConfig
    chain_representation: pathlib.Path | None = None
    title_md: pathlib.Path | None = None
    orientation: Orientation | None = None

    @property
    def slug(self) -> str:
        """Filesystem- and ref-safe form of `name`, used inside the archive."""
        return _slug(self.name)


@dataclasses.dataclass(frozen=True)
class Spec:
    """A whole spec file: one structure, one output, and the views to draw."""

    structure: str
    out: pathlib.Path
    views: tuple[View, ...]
    assembly: str = "au"
    on_mismatch: str = "report"
    viewer_height: str = "70vh"
    molstar_ui: str = "show"


def _slug(name: str) -> str:
    """A conservative identifier from a view name.

    Used for the annotation member name and the MVS node ref, so it must be safe
    in both a zip path and a Mol* cell tag.
    """
    kept = [character if character.isalnum() else "-" for character in name.lower()]
    slug = "".join(kept).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug


def _require_mapping(value, what: str, path: pathlib.Path) -> dict:
    if not isinstance(value, dict):
        raise InputError(
            f"{path}: {what} must be a mapping, got {type(value).__name__}"
        )
    return value


def _check_keys(given, allowed, what: str, path: pathlib.Path) -> None:
    unknown = sorted(set(given) - set(allowed))
    if unknown:
        raise InputError(
            f"{path}: unknown {what} {unknown}; allowed keys are {sorted(allowed)}"
        )


def _as_path(value, key: str, path: pathlib.Path) -> pathlib.Path:
    """Resolve a path key relative to the spec file, not the working directory.

    A spec names files that sit beside it, so it keeps working when run from
    anywhere -- which is what lets an example be a directory you can copy.
    """
    if not isinstance(value, (str, pathlib.Path)):
        raise InputError(f"{path}: {key} must be a path, got {type(value).__name__}")
    candidate = pathlib.Path(value)
    return candidate if candidate.is_absolute() else path.parent / candidate


def _parse_chains(value, path: pathlib.Path) -> tuple[str, ...]:
    """``chains`` as a YAML list, or a comma-separated string."""
    if isinstance(value, str):
        items = [part.strip() for part in value.split(",")]
    elif isinstance(value, list):
        items = [str(item).strip() for item in value]
    else:
        raise InputError(
            f"{path}: chains must be a list or a comma-separated string, got "
            f"{type(value).__name__}"
        )
    chains = tuple(item for item in items if item)
    if not chains:
        raise InputError(f"{path}: chains is empty; omit the key to show every chain")
    return chains


def _vec3(value, key: str, where: str, path: pathlib.Path) -> tuple:
    """Three numbers, however YAML spelled them."""
    if not isinstance(value, list) or len(value) != 3:
        raise InputError(f"{path}: {where} {key} must be a list of 3 numbers")
    out = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise InputError(f"{path}: {where} {key} must be 3 numbers, got {item!r}")
        out.append(float(item))
    return tuple(out)


def _parse_orientation(value, where: str, path: pathlib.Path) -> Orientation:
    """An ``orientation`` block, as written by the page's Copy camera button."""
    raw = _require_mapping(value, f"{where} orientation", path)
    _check_keys(raw, ORIENTATION_KEYS, f"key in {where} orientation", path)
    missing = sorted({"position", "target"} - set(raw))
    if missing:
        raise InputError(
            f"{path}: {where} orientation is missing {missing}. Capture one by "
            "opening the rendered page with #camera appended to the URL and "
            "clicking Copy camera."
        )
    radius = raw.get("radius")
    if radius is not None and (
        isinstance(radius, bool) or not isinstance(radius, (int, float))
    ):
        raise InputError(f"{path}: {where} orientation radius must be a number")
    return Orientation(
        position=_vec3(raw["position"], "position", where, path),
        target=_vec3(raw["target"], "target", where, path),
        up=_vec3(raw["up"], "up", where, path) if "up" in raw else (0.0, 1.0, 0.0),
        radius=None if radius is None else float(radius),
    )


def _build_view(raw: dict, index: int, path: pathlib.Path) -> View:
    what = f"key in views[{index}]"
    _check_keys(raw, (*REQUIRED_VIEW_KEYS, *OPTIONAL_VIEW_KEYS), what, path)
    missing = sorted(set(REQUIRED_VIEW_KEYS) - set(raw))
    if missing:
        raise InputError(
            f"{path}: views[{index}] is missing {missing}. Every view states its "
            "own options; use a YAML anchor to share them between views."
        )
    name = raw["name"]
    if not isinstance(name, str) or not name.strip():
        raise InputError(f"{path}: views[{index}] name must be a non-empty string")
    if not _slug(name):
        raise InputError(
            f"{path}: views[{index}] name {name!r} has no alphanumeric characters"
        )

    # ViewConfig validates the values themselves, and is the only place that
    # knows the allowed ones.
    config = ViewConfig(
        assembly="au",  # replaced by the spec's shared value in load_spec
        chains=_parse_chains(raw["chains"], path) if "chains" in raw else None,
        default_color=raw["default_color"],
        default_representation=raw["default_representation"],
        waters=raw["waters"],
        ligands=raw["ligands"],
        glycans=raw["glycans"],
        ions=raw["ions"],
    )
    return View(
        name=name.strip(),
        csv=_as_path(raw["csv"], "csv", path),
        config=config,
        chain_representation=(
            _as_path(raw["chain_representation"], "chain_representation", path)
            if "chain_representation" in raw
            else None
        ),
        title_md=(
            _as_path(raw["title_md"], "title_md", path) if "title_md" in raw else None
        ),
        orientation=(
            _parse_orientation(raw["orientation"], f"views[{index}]", path)
            if "orientation" in raw
            else None
        ),
    )


def load_spec(path: str | pathlib.Path) -> Spec:
    """Read and validate a spec file.

    Parameters
    ----------
    path
        The YAML file. Paths inside it resolve relative to it.

    Returns
    -------
    Spec
        The parsed spec, with every view's options already validated by
        `prot_struct_viz.ViewConfig`.

    Raises
    ------
    InputError
        On anything the file gets wrong, naming the key at fault.
    """
    path = pathlib.Path(path)
    if not path.is_file():
        raise InputError(f"no such file: {path}")
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as err:
        raise InputError(f"{path}: not valid YAML: {err}") from err
    if document is None:
        raise InputError(f"{path}: is empty")
    document = _require_mapping(document, "the spec", path)

    _check_keys(
        document,
        (*SHARED_KEYS, *OPTIONAL_SHARED_KEYS, DEFINITIONS_KEY, "views"),
        "top-level key",
        path,
    )
    missing = sorted({*SHARED_KEYS, "views"} - set(document))
    if missing:
        raise InputError(f"{path}: missing top-level {missing}")

    raw_views = document["views"]
    if not isinstance(raw_views, list) or not raw_views:
        raise InputError(f"{path}: views must be a non-empty list")

    views = []
    for index, raw in enumerate(raw_views):
        views.append(
            _build_view(_require_mapping(raw, f"views[{index}]", path), index, path)
        )

    for attribute, label in (("name", "name"), ("slug", "name (once simplified)")):
        seen = {}
        for view in views:
            value = getattr(view, attribute)
            if value in seen:
                raise InputError(
                    f"{path}: two views share the {label} {value!r}; the selector "
                    "would not be able to tell them apart"
                )
            seen[value] = True

    structure = document["structure"]
    if not isinstance(structure, str) or not structure.strip():
        raise InputError(f"{path}: structure must be a non-empty string")
    assembly = str(document["assembly"])

    # assembly and on_mismatch are shared, so they are stamped onto every view's
    # config rather than left at the placeholder _build_view used. That keeps a
    # View's config a complete, truthful description of how that view is built.
    # ViewConfig validates on_mismatch, being the only place that knows the allowed
    # modes; `assembly` cannot be checked without the structure, so it is checked
    # by structure.get_assembly_chains once the entry has been read.
    on_mismatch = document["on_mismatch"]
    views = tuple(
        dataclasses.replace(
            view,
            config=dataclasses.replace(
                view.config, assembly=assembly, on_mismatch=on_mismatch
            ),
        )
        for view in views
    )

    viewer_height = str(document.get("viewer_height", "70vh")).strip()
    if not _CSS_LENGTH.match(viewer_height):
        raise InputError(
            f"{path}: viewer_height {viewer_height!r} is not a CSS length; use a "
            "number with one of px, rem, em, vh, %"
        )
    molstar_ui = document.get("molstar_ui", "show")
    if molstar_ui not in ("show", "hide"):
        raise InputError(
            f"{path}: molstar_ui must be one of ['show', 'hide'], got {molstar_ui!r}"
        )

    return Spec(
        structure=structure.strip(),
        out=_as_path(document["out"], "out", path),
        views=views,
        assembly=assembly,
        on_mismatch=on_mismatch,
        viewer_height=viewer_height,
        molstar_ui=molstar_ui,
    )
