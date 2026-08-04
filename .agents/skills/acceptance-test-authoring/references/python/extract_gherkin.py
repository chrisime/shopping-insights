#!/usr/bin/env python3
"""Extracts classic Gherkin from Markdown specs (spec.md) into .feature files.

A spec.md holds prose plus Gherkin inside column-0 ```gherkin fences. The
extraction copies every line inside a gherkin fence VERBATIM at its original
position and turns every other line (prose, fence markers, bodies of
non-gherkin fences) into an empty line. The output therefore has the IDENTICAL
line count to the input: line N of the extracted .feature is line N of the
spec.md. gherkin-lint messages, behave failure locations and effective-spec
reporting all point at valid spec.md lines with no translation. NEVER
"improve" this to collapse blank lines -- that invariant is what the whole
toolchain leans on.

Fences follow CommonMark: an opener is 3+ backticks at column 0 with info
string exactly `gherkin`; the closer is at least as many backticks at column 0.
Non-gherkin fences are tracked too, so a ```gherkin quoted inside a longer
documentation fence cannot false-trigger. Gherkin docstrings delimited by ```
are safe: they are always indented, and the closer regex requires column 0.

Failure modes are loud, never silent: an unclosed fence, a spec.md with no
gherkin fence, or an INDENTED ```gherkin opener (which would otherwise
silently drop its scenarios from the suite) are hard errors.

This is the Python-stack peer of javascript/extract-gherkin.cjs. The two MUST
stay behaviourally identical -- same regexes, same hard errors, same blanking.
See the skill's "Port parity" note before changing either.

Deliberately dependency-free (stdlib only) and 3.8+ compatible: the CLI form
must run from the skill's references/python/ directory, where no virtualenv
exists.
"""

import re
import shutil
import sys
from pathlib import Path

GHERKIN_OPEN_RE = re.compile(r"^(`{3,})gherkin\s*$")
ANY_OPEN_RE = re.compile(r"^(`{3,})\S*\s*$")
INDENTED_GHERKIN_RE = re.compile(r"^\s+`{3,}gherkin\s*$")


class ExtractionError(Exception):
    """A spec.md could not be extracted. Always names file:line."""


def extract_file(md_path):
    """Returns the extracted .feature text for one spec.md, line count preserved."""
    md_path = Path(md_path)
    lines = re.split(r"\r?\n", md_path.read_text(encoding="utf-8"))
    out = []
    state = "prose"  # 'prose' | 'gherkin' | 'other-fence'
    fence_ticks = 0
    open_line = 0
    gherkin_fences = 0
    close_re = None

    for i, line in enumerate(lines):
        if state == "prose":
            m = GHERKIN_OPEN_RE.match(line)
            if m:
                state = "gherkin"
                fence_ticks = len(m.group(1))
                close_re = re.compile(r"^`{%d,}\s*$" % fence_ticks)
                open_line = i + 1
                gherkin_fences += 1
                out.append("")
            elif INDENTED_GHERKIN_RE.match(line):
                raise ExtractionError(
                    "%s:%d: indented ```gherkin fence — gherkin fences must "
                    "start at column 0" % (md_path, i + 1)
                )
            else:
                m = ANY_OPEN_RE.match(line)
                if m:
                    state = "other-fence"
                    fence_ticks = len(m.group(1))
                    close_re = re.compile(r"^`{%d,}\s*$" % fence_ticks)
                    open_line = i + 1
                out.append("")
            continue

        if close_re.match(line):
            state = "prose"
            out.append("")
        else:
            out.append(line if state == "gherkin" else "")

    if state != "prose":
        raise ExtractionError("%s:%d: unclosed fence" % (md_path, open_line))
    if gherkin_fences == 0:
        raise ExtractionError(
            "%s: no ```gherkin fences found — a spec.md must contain gherkin" % md_path
        )
    if len(out) != len(lines):
        raise ExtractionError("%s: line-count invariant violated (extractor bug)" % md_path)
    return "\n".join(out)


def _walk(root, directory, basename, found):
    """Collects files named <basename> under <directory>, as posix paths
    relative to <root>. '*.ext' is supported as a suffix match."""
    if not directory.is_dir():
        return found
    for entry in sorted(directory.iterdir()):
        if entry.is_dir():
            _walk(root, entry, basename, found)
        elif entry.name == basename or (
            basename.startswith("*.") and entry.name.endswith(basename[1:])
        ):
            found.append(entry.relative_to(root).as_posix())
    return found


def collect_spec_sources(openspec_dir, basename):
    """Spec roots: specs/ (source of truth) and each active change's specs/ --
    changes/archive/ is excluded structurally (archive nests one level deeper
    than changes/<id>/) plus a defensive filter on the collected paths."""
    openspec_dir = Path(openspec_dir)
    found = _walk(openspec_dir, openspec_dir / "specs", basename, [])
    changes_dir = openspec_dir / "changes"
    if changes_dir.is_dir():
        for entry in sorted(changes_dir.iterdir()):
            if not entry.is_dir() or entry.name == "archive":
                continue
            _walk(openspec_dir, entry / "specs", basename, found)
    return sorted(p for p in found if "changes/archive/" not in p)


def extract_all(openspec_dir=None, out_dir=None):
    """Extracts every spec.md under <openspec_dir> (source of truth + active
    change deltas, archive excluded) into <out_dir>, mirroring the
    openspec-relative path with spec.md -> spec.feature. The output dir is
    wiped first -- a stale extraction would keep deleted or renamed
    capabilities executing."""
    here = Path(__file__).resolve().parent
    openspec_dir = Path(openspec_dir).resolve() if openspec_dir else (here / ".." / "openspec").resolve()
    out_dir = Path(out_dir).resolve() if out_dir else (here / ".extracted").resolve()

    shutil.rmtree(out_dir, ignore_errors=True)

    sources = collect_spec_sources(openspec_dir, "spec.md")

    # Legacy-format tripwire: raw .feature files under openspec/ no longer run
    # anywhere -- flag them instead of letting them silently drop out.
    legacy = collect_spec_sources(openspec_dir, "*.feature")
    if legacy:
        sys.stderr.write(
            "[extract-gherkin] WARNING: legacy .feature file(s) under openspec/ "
            "are ignored (specs are spec.md now): %s\n" % ", ".join(legacy)
        )

    written = []
    for rel in sources:
        dest = out_dir / re.sub(r"spec\.md$", "spec.feature", rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(extract_file(openspec_dir / rel), encoding="utf-8")
        written.append(dest)
    return out_dir, written


# CLI: python extract_gherkin.py [openspecDir] [outDir]
if __name__ == "__main__":
    try:
        out, written_files = extract_all(
            sys.argv[1] if len(sys.argv) > 1 else None,
            sys.argv[2] if len(sys.argv) > 2 else None,
        )
        sys.stderr.write(
            "[extract-gherkin] %d spec.md file(s) extracted to %s\n" % (len(written_files), out)
        )
    except ExtractionError as err:
        sys.stderr.write("[extract-gherkin] %s\n" % err)
        sys.exit(1)
