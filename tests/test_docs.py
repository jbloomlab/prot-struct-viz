"""Tests for the prose: rules that a reader cannot see broken until it ships."""

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).parent.parent

#: Markdown we author and ship. Deliberately not a recursive glob: it would sweep
#: .venv/, site/, and the coding-standards submodule, none of which are ours. Files
#: starting with "_" are scratch, ignored by the repo's `/_*` rule.
MARKDOWN_FILES = sorted(
    p
    for p in [*REPO_ROOT.glob("*.md"), *(REPO_ROOT / "docs").glob("**/*.md")]
    if not p.name.startswith("_")
)

#: ``Mol*`` with the asterisk left unescaped.
UNESCAPED_MOLSTAR = re.compile(r"Mol(?<!\\)\*")

#: An inline code span. Markdown does no emphasis processing inside one, so a
#: bare ``Mol*`` there is literal and correct -- including where the rule below
#: is being written down.
CODE_SPAN = re.compile(r"`[^`]*`")


def _prose_lines(text: str):
    """Yield ``(line_number, line)`` for prose only.

    Fenced blocks and inline code spans are dropped: emphasis is not parsed
    inside either, so an asterisk there means an asterisk.
    """
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        yield number, CODE_SPAN.sub("", line)


def test_markdown_files_are_discoverable():
    """Guard the glob: a bad filter would make every sweep here vacuous."""
    names = {p.name for p in MARKDOWN_FILES}
    assert {"README.md", "CHANGELOG.md", "index.md"} <= names


def test_molstar_asterisk_is_escaped():
    """A bare ``Mol*`` silently italicizes the wrong span.

    Python-Markdown -- unlike CommonMark, whose flanking rules reject it --
    pairs the asterisk in ``Mol*`` with the next ``*`` in the same paragraph.
    That once rendered the docs home page as "the Mol UI ... is the initial*
    state", with the emphasis on the wrong words and a stray asterisk left
    over. Escaping it everywhere is the only rule that does not depend on
    nobody ever adding emphasis to a paragraph that mentions Mol*.
    """
    offenders = [
        f"{path.relative_to(REPO_ROOT)}:{number}"
        for path in MARKDOWN_FILES
        for number, line in _prose_lines(path.read_text())
        if UNESCAPED_MOLSTAR.search(line)
    ]
    assert not offenders, "write Mol\\* instead:\n" + "\n".join(offenders)


def test_the_molstar_check_can_actually_fail():
    """Negative control: a filter this aggressive could pass by finding nothing."""
    prose = dict(_prose_lines("the Mol* UI\n\n```\nMol* in a fence\n```\n"))
    assert any(UNESCAPED_MOLSTAR.search(line) for line in prose.values())
    assert not any("fence" in line for line in prose.values())
    assert not UNESCAPED_MOLSTAR.search(dict(_prose_lines("a `Mol*` span"))[1])
    assert not UNESCAPED_MOLSTAR.search(dict(_prose_lines(r"the Mol\* UI"))[1])
