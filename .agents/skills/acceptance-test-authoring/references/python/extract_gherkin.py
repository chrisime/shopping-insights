#!/usr/bin/env python3
"""Extract classic Gherkin from Markdown specs into .feature files."""

import re
import shutil
import sys
from pathlib import Path

GHERKIN_OPEN_RE = re.compile(r"^(`{3,})gherkin\s*$")
ANY_OPEN_RE = re.compile(r"^(`{3,})\S*\s*$")
INDENTED_GHERKIN_RE = re.compile(r"^\s+`{3,}gherkin\s*$")


class ExtractionError(Exception):
    """A spec.md could not be extracted."""


def extract_file(md_path):
    md_path = Path(md_path)
    lines = re.split(r"\r?\n", md_path.read_text(encoding="utf-8"))
    out = []
    state = "prose"
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
                    "%s:%d: indented ```gherkin fence; gherkin fences must start at column 0"
                    % (md_path, i + 1)
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
        raise ExtractionError("%s: no ```gherkin fences found; a spec.md must contain gherkin" % md_path)
    if len(out) != len(lines):
        raise ExtractionError("%s: line-count invariant violated (extractor bug)" % md_path)
    return "\n".join(out)


def _walk(root, directory, basename, found):
    if not directory.is_dir():
        return found
    for entry in sorted(directory.iterdir()):
        if entry.is_dir():
            _walk(root, entry, basename, found)
        elif entry.name == basename or (basename.startswith("*.") and entry.name.endswith(basename[1:])):
            found.append(entry.relative_to(root).as_posix())
    return found


def collect_spec_sources(openspec_dir, basename):
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
    here = Path(__file__).resolve().parent
    openspec_dir = Path(openspec_dir).resolve() if openspec_dir else (here / ".." / "openspec").resolve()
    out_dir = Path(out_dir).resolve() if out_dir else (here / ".extracted").resolve()

    shutil.rmtree(out_dir, ignore_errors=True)
    sources = collect_spec_sources(openspec_dir, "spec.md")

    legacy = collect_spec_sources(openspec_dir, "*.feature")
    if legacy:
        sys.stderr.write(
            "[extract-gherkin] WARNING: legacy .feature file(s) under openspec/ are ignored: %s\n"
            % ", ".join(legacy)
        )

    written = []
    for rel in sources:
        dest = out_dir / re.sub(r"spec\.md$", "spec.feature", rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(extract_file(openspec_dir / rel), encoding="utf-8")
        written.append(dest)
    return out_dir, written


if __name__ == "__main__":
    try:
        out, written_files = extract_all(
            sys.argv[1] if len(sys.argv) > 1 else None,
            sys.argv[2] if len(sys.argv) > 2 else None,
        )
        sys.stderr.write("[extract-gherkin] %d spec.md file(s) extracted to %s\n" % (len(written_files), out))
    except ExtractionError as err:
        sys.stderr.write("[extract-gherkin] %s\n" % err)
        sys.exit(1)
