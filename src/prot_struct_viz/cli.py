"""The ``prot-struct-viz`` command line interface.

A thin wrapper around `prot_struct_viz.render`: it turns flags into a
`prot_struct_viz._config.ViewConfig` and reports failures without a
traceback. Help text comes from `prot_struct_viz._config.OPTION_DOCS`, so
the CLI and the Python API describe every option the same way.
"""

from __future__ import annotations

import pathlib
import sys

import click

from . import render
from ._config import (
    DEFAULT_CACHE_DIR,
    DEFAULT_COLOR,
    DEFAULT_REPRESENTATION,
    MISMATCH_MODES,
    OPTION_DOCS,
    REPRESENTATIONS,
    InputError,
    ViewConfig,
)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--structure", required=True, help=OPTION_DOCS["structure"])
@click.option(
    "--csv",
    required=True,
    type=click.Path(path_type=pathlib.Path),
    help=OPTION_DOCS["csv"],
)
@click.option(
    "--out",
    required=True,
    type=click.Path(path_type=pathlib.Path),
    help=OPTION_DOCS["out"],
)
@click.option(
    "--assembly", default="au", show_default=True, help=OPTION_DOCS["assembly"]
)
@click.option("--chains", default=None, help=OPTION_DOCS["chains"])
@click.option(
    "--on-mismatch",
    type=click.Choice(MISMATCH_MODES),
    default="report",
    show_default=True,
    help=OPTION_DOCS["on_mismatch"],
)
@click.option(
    "--default-color",
    default=DEFAULT_COLOR,
    show_default=True,
    help=OPTION_DOCS["default_color"],
)
@click.option(
    "--default-representation",
    type=click.Choice(sorted(REPRESENTATIONS)),
    default=DEFAULT_REPRESENTATION,
    show_default=True,
    help=OPTION_DOCS["default_representation"],
)
@click.option(
    "--chain-representation",
    type=click.Path(path_type=pathlib.Path),
    default=None,
    help=OPTION_DOCS["chain_representation"],
)
@click.option(
    "--waters",
    type=click.Choice(["hide", "show"]),
    default="hide",
    show_default=True,
    help=OPTION_DOCS["waters"],
)
@click.option(
    "--ligands",
    type=click.Choice(["show", "hide"]),
    default="show",
    show_default=True,
    help=OPTION_DOCS["ligands"],
)
@click.option(
    "--glycans",
    type=click.Choice(["snfg", "hide"]),
    default="snfg",
    show_default=True,
    help=OPTION_DOCS["glycans"],
)
@click.option(
    "--ions",
    type=click.Choice(["show", "hide"]),
    default="show",
    show_default=True,
    help=OPTION_DOCS["ions"],
)
@click.option(
    "--title-md",
    type=click.Path(path_type=pathlib.Path),
    default=None,
    help=OPTION_DOCS["title_md"],
)
@click.option(
    "--cache-dir",
    type=click.Path(path_type=pathlib.Path),
    default=DEFAULT_CACHE_DIR,
    show_default=True,
    help=OPTION_DOCS["cache_dir"],
)
def main(
    structure,
    csv,
    out,
    assembly,
    chains,
    on_mismatch,
    default_color,
    default_representation,
    chain_representation,
    waters,
    ligands,
    glycans,
    ions,
    title_md,
    cache_dir,
):
    """Render a protein structure as a self-contained static HTML Mol* view."""
    try:
        config = ViewConfig(
            assembly=assembly,
            chains=(
                tuple(c.strip() for c in chains.split(",") if c.strip())
                if chains
                else None
            ),
            on_mismatch=on_mismatch,
            default_color=default_color,
            default_representation=default_representation,
            waters=waters,
            ligands=ligands,
            glycans=glycans,
            ions=ions,
        )
        render(
            structure,
            csv,
            out,
            config=config,
            chain_representation=chain_representation,
            title_md=title_md,
            cache_dir=cache_dir,
        )
    except InputError as err:
        click.echo(f"\nERROR: {err}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
