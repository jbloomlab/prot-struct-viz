"""The ``prot-struct-viz`` command line interface.

A thin wrapper around `prot_struct_viz.render_file`: it takes one YAML spec
file and reports failures without a traceback. Every option lives in that file
rather than in a flag, so the command has nothing to document that
`prot_struct_viz.spec` does not already describe.
"""

from __future__ import annotations

import pathlib
import sys

import click

from . import __version__, render_file
from ._config import InputError


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "spec",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
@click.version_option(__version__)
def main(spec):
    """Render a protein structure as a self-contained static HTML Mol* view.

    SPEC is a YAML file describing one page: the structure to draw, where to
    write the HTML, and one or more named views of it. See the spec reference
    in the docs for every key it may carry.
    """
    try:
        render_file(spec)
    except InputError as err:
        click.echo(f"\nERROR: {err}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
