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

#: A link into this repository on GitHub, capturing the repo-relative path. Both
#: ``blob`` (a file) and ``tree`` (a directory) forms appear in ``docs/examples.md``.
REPO_LINK = re.compile(
    r"https://github\.com/jbloomlab/prot-struct-viz/(?:blob|tree)/main/([^)\s#]+)"
)

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


def test_every_option_reaches_the_spec_reference():
    """The loader knows every key; the reference page is where readers meet one.

    An option that never reaches the docs is invisible, and the spec format has no
    ``--help`` to fall back on.
    """
    from prot_struct_viz.spec import OPTION_KEYS

    reference = (REPO_ROOT / "docs" / "spec.md").read_text()
    missing = [key for key in OPTION_KEYS if f"`{key}`" not in reference]
    assert not missing, f"docs/spec.md does not mention {missing}"


def test_linked_repo_files_exist():
    """A ``blob/main/`` or ``tree/main/`` link is not checked by anything else.

    `mkdocs build --strict` validates relative links between doc pages, but a
    link out to the repository on GitHub is just a URL to it. `docs/examples.md`
    is built out of them: it names each example's inputs instead of inlining
    them, which it used to do via `pymdownx.snippets`. Inlining could not go
    stale; a link can, so this is what replaces that guarantee.
    """
    offenders = [
        f"{path.relative_to(REPO_ROOT)}:{number}: {target}"
        for path in MARKDOWN_FILES
        for number, line in enumerate(path.read_text().splitlines(), start=1)
        for target in REPO_LINK.findall(line)
        if not (REPO_ROOT / target).exists()
    ]
    assert not offenders, "linked repo path does not exist:\n" + "\n".join(offenders)


def test_the_repo_link_check_can_actually_fail():
    """Negative control: the sweep above is only as good as this regex."""
    found = REPO_LINK.findall(
        "see [`spec.yaml`](https://github.com/jbloomlab/prot-struct-viz/blob/main/"
        "examples/1f8b_active_site/spec.yaml) and "
        "[the dir](https://github.com/jbloomlab/prot-struct-viz/tree/main/examples)"
    )
    assert found == ["examples/1f8b_active_site/spec.yaml", "examples"]
    assert REPO_LINK.findall("https://github.com/molstar/molstar") == []
