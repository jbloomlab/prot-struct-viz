"""The render pipeline: a parsed `prot_struct_viz.Spec` to a written HTML file.

Internal: the entry points are `prot_struct_viz.render` and
`prot_struct_viz.render_file`, re-exported from the package root. The module is
underscore-named so that neither shadows the other.

One pass over the spec's views, sharing one download and one parse of the
structure. Everything a view needs is collected here and handed to
`prot_struct_viz.viewer` to become the MVS state; the progress log and the
mismatch report are written as it goes, so a run that aborts still leaves a
record of everything up to the error.
"""

from __future__ import annotations

import pathlib

from ._config import InputError
from .report import Reporter, display_path, report_path_for
from .residues import keys, parse_chain_representations, parse_csv
from .spec import Spec, load_spec
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
from .viewer import (
    ViewBuild,
    build_annotations,
    build_mvsx,
    build_state,
    render_html,
    render_title,
    view_ref,
)


def render_file(
    spec_path: str | pathlib.Path, out: str | pathlib.Path | None = None
) -> pathlib.Path:
    """Load a YAML spec file and render it. What the CLI does.

    Parameters
    ----------
    spec_path
        The YAML spec file.
    out
        Output HTML file, resolved relative to the working directory rather than
        to the spec file. Exactly one of this and the spec's own ``out`` key must
        be given.

    Returns
    -------
    pathlib.Path
        The path written.
    """
    return render(load_spec(spec_path, out=out))


def render(spec: Spec) -> pathlib.Path:
    """Render one spec to a self-contained HTML file.

    Parameters
    ----------
    spec
        The parsed spec: one structure, one output path, and one or more views.

    Returns
    -------
    pathlib.Path
        The path written.

    Raises
    ------
    InputError
        On invalid input, or on a mismatch fatal under the spec's
        ``on_mismatch``. The report file is written either way.
    """
    out_path = pathlib.Path(spec.out)
    report_path = report_path_for(out_path)

    with Reporter(report_path) as reporter:
        reporter.log(f"structure source: {spec.structure}")
        coordinate_text, fmt = resolve_structure(spec.structure)
        reporter.log(f"format: {fmt}")

        parsed = load_structure(coordinate_text, fmt)
        available = assembly_names(parsed)
        reporter.log(f"assemblies defined: {available or '(none)'}")
        reporter.log(f"assembly used: {spec.assembly}")
        reporter.log(f"rendering style: {spec.style}")

        all_counts = residue_counts(parsed)
        reporter.log(f"chains found: {sorted(all_counts)}")
        for chain in sorted(all_counts):
            reporter.log(f"  chain {chain}: {all_counts[chain]} residues")

        # Validation compares each CSV against the whole deposited model, so it
        # does not shift when a view's chains narrow what that view draws.
        deposited_all = get_deposited_residues(parsed)
        assembly_chains = get_assembly_chains(parsed, spec.assembly)
        reporter.log(f"views: {[view.name for view in spec.views]}")

        builds: list[ViewBuild] = []
        rows_by_slug: dict[str, list[dict]] = {}
        captions: list[dict] = []
        wanted_labels: set = set()
        fatal = False

        for view in spec.views:
            config = view.config
            orientation = (
                view.orientation.as_dict() if view.orientation is not None else None
            )
            reporter.log("")
            reporter.log(f"=== view: {view.name} ===")

            display_chains = list(config.chains) if config.chains else None
            deposited = get_deposited_residues(parsed, display_chains)
            reporter.log(f"chains displayed: {sorted({c for c, _ in deposited})}")

            class_counts: dict[str, int] = {}
            for residue_class in deposited.values():
                class_counts[residue_class] = class_counts.get(residue_class, 0) + 1
            reporter.log(
                f"residue classes displayed: {dict(sorted(class_counts.items()))}"
            )
            reporter.log(
                f"heteroatom baseline: waters={config.waters} "
                f"ligands={config.ligands} glycans={config.glycans} "
                f"ions={config.ions}"
            )
            reporter.log(f"base representation: {config.default_representation}")

            chain_overrides = (
                parse_chain_representations(view.chain_representation)
                if view.chain_representation is not None
                else {}
            )
            if chain_overrides:
                reporter.log(f"per-chain representations: {chain_overrides}")

            coloring = parse_csv(view.csv)
            reporter.log(f"CSV: {display_path(view.csv)}, {len(coloring.specs)} rows")

            report = validate(coloring, deposited_all, assembly_chains)
            reporter.write_validation(report)
            fatal = fatal or report.is_fatal(spec.on_mismatch)

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
                    f"WARNING: {len(not_displayed)} CSV row(s) name residues on "
                    "chains this view excludes from the display"
                )

            rows = build_annotations(coloring, deposited, config, chain_overrides)
            rows_by_slug[view.slug] = rows
            # Persistent labels are placed at explicit coordinates, and replicated
            # onto each symmetry copy by the assembly's own transforms.
            labels = (
                coloring,
                deposited,
                residue_centroids(parsed, display_chains),
                assembly_instance_transforms(parsed, spec.assembly),
            )
            builds.append(
                ViewBuild(slug=view.slug, config=config, rows=rows, labels=labels)
            )
            wanted_labels |= {
                (view.slug, spec_.key) for spec_ in coloring.specs if spec_.show_label
            }
            captions.append(
                {
                    "name": view.name,
                    "slug": view.slug,
                    # The page resolves this through queryMVSRef; it must be the
                    # same string build_state put on the structure node.
                    "ref": view_ref(view.slug),
                    "caption": render_title(view.title_md),
                    "orientation": orientation,
                }
            )

        if fatal:
            raise InputError(
                f"on_mismatch is {spec.on_mismatch!r} and a CSV does not match "
                f"the structure; see {display_path(report_path)}"
            )

        structure_member = "structure.cif" if fmt == "mmcif" else "structure.pdb"
        # The page opens on the first view, so its camera is the one MVS can hold.
        state, unplaced = build_state(
            builds, fmt, structure_member, captions[0]["orientation"]
        )
        for view in spec.views:
            if unplaced[view.slug]:
                reporter.log("")
                reporter.log(
                    f"WARNING: view {view.name!r}: {len(unplaced[view.slug])} row(s) "
                    "ask for a persistent label on a residue that is not displayed, "
                    "so no label was drawn"
                )
        mvsx = build_mvsx(state, coordinate_text, structure_member, rows_by_slug)

        # Offer the Labels checkbox only if a label was actually drawn somewhere:
        # rows asking for one on a residue a view excludes leave nothing to move.
        drawn = wanted_labels - {
            (slug, key) for slug, missing in unplaced.items() for key in missing
        }
        html = render_html(
            mvsx,
            captions,
            out_path.stem,
            show_label_toggle=bool(drawn),
            viewer_height=spec.viewer_height,
            molstar_ui=spec.molstar_ui,
            style=spec.style,
        )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        reporter.log("")
        reporter.log(f"wrote {display_path(out_path)} ({len(html) / 1e6:.2f} MB)")
        reporter.log(f"wrote {display_path(report_path)}")

    return out_path
