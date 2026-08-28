# Python API

The CLI is a thin wrapper around [`render_file`](#prot_struct_viz.render_file), which
loads a [spec file](cli.md) and calls [`render`](#prot_struct_viz.render). Both paths go
through the same [`Spec`](#prot_struct_viz.Spec), so they cannot disagree about what an
option does.

```python
from prot_struct_viz import render_file

render_file("spec.yaml")
```

To build a spec in Python instead of reading one, construct it directly. `ViewConfig`
keeps its defaults here — the "no defaults" rule is a property of the spec *file*, which
has to be readable on its own, not of the dataclass:

```python
import pathlib

from prot_struct_viz import Spec, View, ViewConfig, render

render(
    Spec(
        structure="1F8B",
        out=pathlib.Path("view.html"),
        assembly="1",
        views=(
            View(
                name="Active site",
                csv=pathlib.Path("coloring.csv"),
                config=ViewConfig(assembly="1", waters="hide"),
                title_md=pathlib.Path("title.md"),
            ),
        ),
    )
)
```

`assembly` and `on_mismatch` appear on both `Spec` and each view's `ViewConfig`: they are
shared settings, and `load_spec` stamps them onto every view so a view's config is a
complete description of how that view is built. Constructing a `Spec` by hand, keep them
in step.

::: prot_struct_viz.render_file
    options:
      show_root_full_path: false

::: prot_struct_viz.render
    options:
      show_root_full_path: false

::: prot_struct_viz.load_spec
    options:
      show_root_full_path: false

::: prot_struct_viz.Spec

::: prot_struct_viz.View

::: prot_struct_viz.ViewConfig

::: prot_struct_viz.InputError
