"""Build the worked example from the README.

Renders influenza B neuraminidase (PDB 1F8B) with the active-site residues that
contact the DANA inhibitor colored by distance. Writes into ``examples/output/``,
which is gitignored -- the HTML is regenerable and too large to track.

    python examples/build_example.py
"""

import pathlib

from prot_struct_viz import ViewConfig, render

HERE = pathlib.Path(__file__).parent
OUTPUT_DIR = HERE / "output"

#: The biological tetramer, generated in the browser from crystal symmetry.
ASSEMBLY = "1"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    render(
        "1F8B",
        HERE / "coloring.csv",
        OUTPUT_DIR / "1f8b_active_site.html",
        config=ViewConfig(assembly=ASSEMBLY, waters="hide"),
        chain_representation=HERE / "chains.csv",
        title_md=HERE / "title.md",
    )


if __name__ == "__main__":
    main()
