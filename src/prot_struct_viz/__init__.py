"""Render a protein structure as a self-contained static HTML Mol* view.

The whole input is one YAML spec file: see `prot_struct_viz.spec`. `render`
takes the parsed `Spec`, and the ``prot-struct-viz`` CLI is a thin wrapper that
loads a file and calls it, so the two surfaces cannot disagree.

A spec may hold several named **views** of one structure. They are all drawn
into the page up front and the selector only changes which is visible, so
switching leaves the camera exactly where the reader put it. The price is that
geometry cost scales with the number of views.
"""

from __future__ import annotations

import importlib.metadata

from ._config import InputError, ViewConfig
from ._render import render, render_file
from .spec import Orientation, Spec, View, load_spec

#: Read from the installed distribution metadata, so pyproject.toml's ``version``
#: is the only place a release number is written.
__version__ = importlib.metadata.version("prot-struct-viz")

__all__ = [
    "InputError",
    "Orientation",
    "Spec",
    "View",
    "ViewConfig",
    "load_spec",
    "render",
    "render_file",
    "__version__",
]
