# Python API

The CLI is a thin wrapper around [`render`](#prot_struct_viz.render). Both take the same
[`ViewConfig`](#prot_struct_viz.ViewConfig), so they cannot disagree about what an option
does.

```python
from prot_struct_viz import ViewConfig, render

render(
    "1F8B",
    "examples/coloring.csv",
    "view.html",
    config=ViewConfig(assembly="1", waters="hide"),
    title_md="examples/title.md",
)
```

::: prot_struct_viz.render
    options:
      show_root_full_path: false

::: prot_struct_viz.ViewConfig

::: prot_struct_viz.InputError
