"""Write the progress log and mismatch report to stdout and to a file.

The report file is always written, including when the run aborts, so a failed
run still leaves a record of everything up to the error. That is why the
`Reporter` is opened before any other work and closed in a ``finally``.
"""

from __future__ import annotations

import pathlib
import sys

from ._config import InputError
from .validate import ValidationReport

#: Suffix replacing ``.html`` to give the report path.
REPORT_SUFFIX = "_report.txt"


def display_path(path: pathlib.Path) -> str:
    """Render a path for the log, relative to the working directory where it helps.

    A path under the working directory reads better relative -- it is what the
    user typed, and it keeps the report portable. Anything outside stays
    absolute, since a long chain of ``..`` is worse than the full path.
    """
    path = pathlib.Path(path)
    try:
        return str(path.resolve().relative_to(pathlib.Path.cwd()))
    except ValueError:
        return str(path)


def report_path_for(out_path: pathlib.Path) -> pathlib.Path:
    """The report path for an output HTML path (``fig.html`` -> ``fig_report.txt``).

    Raises
    ------
    InputError
        If the output path does not end in ``.html``, which would leave the
        report path ambiguous.
    """
    out_path = pathlib.Path(out_path)
    if out_path.suffix.lower() != ".html":
        raise InputError(f"--out must end in '.html', got {out_path.name!r}")
    return out_path.with_name(out_path.stem + REPORT_SUFFIX)


class Reporter:
    """Writes progress and validation output to stdout and to the report file."""

    def __init__(self, report_path: pathlib.Path, stream=None):
        self.report_path = pathlib.Path(report_path)
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.report_path, "w", encoding="utf-8")
        self._stream = sys.stdout if stream is None else stream

    def log(self, line: str = "") -> None:
        """Write one line to both stdout and the report file."""
        print(line, file=self._stream)
        print(line, file=self._file)
        self._file.flush()

    def write_validation(self, report: ValidationReport) -> None:
        """Write the mismatch report to both sinks."""
        self.log()
        self.log(report.format())

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()
        return False
