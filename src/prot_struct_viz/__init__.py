"""Render a protein structure as a self-contained static HTML Mol* view.

The public entry point is `render`, which the ``prot-struct-viz`` CLI is a
thin wrapper around. Both take the same `ViewConfig`, so the two surfaces
cannot disagree about what an option does.
"""

from __future__ import annotations

import pathlib

from ._config import DEFAULT_CACHE_DIR, InputError, ViewConfig
from .viewer import (
    build_annotations,
    build_mvsx,
    build_state,
    render_html,
    render_title,
)
from .report import Reporter, display_path, report_path_for
from .residues import keys, parse_chain_representations, parse_csv
from .structure import (
    addressable_residues,
    assembly_instance_transforms,
    assembly_names,
    get_assembly_chains,
    get_deposited_residues,
    load_structure,
    residue_centroids,
    residue_counts,
    resolve_structure,
)
from .validate import validate

__version__ = "0.1.0"

__all__ = ["InputError", "ViewConfig", "render", "__version__"]


def render(
    structure: str,
    csv: str | pathlib.Path,
    out: str | pathlib.Path,
    *,
    config: ViewConfig | None = None,
    chain_representation: str | pathlib.Path | None = None,
    title_md: str | pathlib.Path | None = None,
    cache_dir: str | pathlib.Path = DEFAULT_CACHE_DIR,
) -> pathlib.Path:
    """Render one structure to a self-contained HTML file.

    Parameters
    ----------
    structure
        A PDB ID to fetch from RCSB, or a path to a local ``.cif``/``.pdb`` file.
    csv
        Path to the residue color/label/representation table.
    out
        Path of the HTML file to write. Must end in ``.html``; the mismatch
        report is written alongside it as ``<stem>_report.txt``.
    config
        View options. Defaults to `ViewConfig` defaults.
    chain_representation
        Optional path to a ``chain,representation`` override file.
    title_md
        Optional path to a Markdown file rendered above the viewer.
    cache_dir
        Where structures fetched from RCSB are cached.

    Returns
    -------
    pathlib.Path
        The path written.

    Raises
    ------
    InputError
        On invalid input or a fatal mismatch under the chosen
        ``on_mismatch`` mode. The report file is written either way.
    """
    config = ViewConfig() if config is None else config
    out_path = pathlib.Path(out)
    report_path = report_path_for(out_path)

    with Reporter(report_path) as reporter:
        reporter.log(f"structure source: {structure}")
        coordinate_text, fmt = resolve_structure(structure, pathlib.Path(cache_dir))
        reporter.log(f"format: {fmt}")

        parsed = load_structure(coordinate_text, fmt)
        available = assembly_names(parsed)
        reporter.log(f"assemblies defined: {available or '(none)'}")
        reporter.log(f"assembly used: {config.assembly}")

        all_counts = residue_counts(parsed)
        reporter.log(f"chains found: {sorted(all_counts)}")
        for chain in sorted(all_counts):
            reporter.log(f"  chain {chain}: {all_counts[chain]} residues")

        # Validation compares the CSV against the whole deposited model, so it does
        # not shift when --chains narrows what is drawn.
        deposited_all = get_deposited_residues(parsed)
        display_chains = list(config.chains) if config.chains else None
        deposited = get_deposited_residues(parsed, display_chains)
        reporter.log(f"chains displayed: {sorted({c for c, _ in deposited})}")

        class_counts: dict[str, int] = {}
        for residue_class in deposited.values():
            class_counts[residue_class] = class_counts.get(residue_class, 0) + 1
        reporter.log(f"residue classes displayed: {dict(sorted(class_counts.items()))}")
        reporter.log(
            f"heteroatom baseline: waters={config.waters} ligands={config.ligands} "
            f"glycans={config.glycans} ions={config.ions}"
        )
        reporter.log(f"base representation: {config.default_representation}")

        chain_overrides = (
            parse_chain_representations(pathlib.Path(chain_representation))
            if chain_representation is not None
            else {}
        )
        if chain_overrides:
            reporter.log(f"per-chain representations: {chain_overrides}")

        coloring = parse_csv(pathlib.Path(csv))
        reporter.log(
            f"CSV: {len(coloring.specs)} rows, schemes {coloring.scheme_names}"
        )

        assembly_chains = get_assembly_chains(parsed, config.assembly)
        report = validate(coloring, deposited_all, assembly_chains, config.on_mismatch)
        reporter.write_validation(report)

        if report.is_fatal(config.on_mismatch):
            raise InputError(
                f"--on-mismatch {config.on_mismatch} and the CSV does not match the "
                f"structure; see {display_path(report_path)}"
            )

        if report.in_csv_not_structure:
            reporter.log("")
            reporter.log(
                f"WARNING: dropping {len(report.in_csv_not_structure)} CSV row(s) "
                "that name no addressable residue in the structure"
            )
        not_displayed = keys(coloring) & (
            addressable_residues(deposited_all) - addressable_residues(deposited)
        )
        if not_displayed:
            reporter.log("")
            reporter.log(
                f"WARNING: {len(not_displayed)} CSV row(s) name residues on chains "
                "that --chains excludes from the display"
            )

        scheme = coloring.scheme_names[0]
        if len(coloring.scheme_names) > 1:
            reporter.log(
                f"WARNING: coloring by scheme {scheme!r}; the other schemes "
                f"{coloring.scheme_names[1:]} are recorded but not yet selectable"
            )

        rows = build_annotations(coloring, deposited, config, chain_overrides)
        structure_member = "structure.cif" if fmt == "mmcif" else "structure.pdb"
        # Persistent labels are placed at explicit coordinates, and replicated onto
        # each symmetry copy by the assembly's own transforms.
        labels = (
            coloring,
            deposited,
            residue_centroids(parsed, display_chains),
            assembly_instance_transforms(parsed, config.assembly),
        )
        state, unplaced_labels = build_state(
            rows, fmt, structure_member, config, scheme, labels=labels
        )
        if unplaced_labels:
            reporter.log("")
            reporter.log(
                f"WARNING: {len(unplaced_labels)} row(s) ask for a persistent label "
                "on a residue that is not displayed, so no label was drawn"
            )
        mvsx = build_mvsx(state, coordinate_text, structure_member, rows)

        title_html = render_title(pathlib.Path(title_md) if title_md else None)
        html = render_html(mvsx, title_html, out_path.stem)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        reporter.log("")
        reporter.log(f"wrote {display_path(out_path)} ({len(html) / 1e6:.2f} MB)")
        reporter.log(f"wrote {display_path(report_path)}")

    return out_path
