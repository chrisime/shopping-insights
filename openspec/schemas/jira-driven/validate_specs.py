#!/usr/bin/env python3
"""Validate jira-driven OpenSpec specs (the jira-driven 'validate' gate).

The OpenSpec CLI's `validate`/`archive` commands only understand the
spec-driven delta headers (`## ADDED Requirements` / `### Requirement:` /
`#### Scenario:`). The `jira-driven` schema authors deltas as fenced Gherkin
with `# @openspec:` markers instead, so the CLI reports every change as having
'no deltas' (a false negative). This module is the schema's own validation
gate, standing in for `openspec validate --strict`:

  - Extraction-side errors (malformed fences, no gherkin fences)
  - gherkin-lint over the extracted output. The `.gherkin-lintrc` is not kept
    in the schema directory; it is provisioned into the repository root at
    invocation time from an existing root rc, the `acceptance-tests/` copy, or
    the acceptance-test-authoring skill's `references/gherkin-lintrc.json`, and
    linting is skipped if no source is available.
  - every `Rule:` in a delta spec carries a `# @openspec:` operation marker
  - every `Rule:` marked ADDED/MODIFIED has at least one `Scenario:`
  - Jira Acceptance Criterion traceability: every `<!-- AC: TICKET-ID#N -->`
    comment maps to at least one Gherkin scenario in the same spec file
  - AC coverage gate (per active change with specs): every AC listed in the
    change's proposal `## Source` maps to an `<!-- AC: TICKET-ID#N -->`
    comment, and every such comment references an AC that exists in `## Source`
    (no orphan comments)
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

GHERKIN_OPEN_RE = re.compile(r"^(`{3,})gherkin\s*$")
ANY_OPEN_RE = re.compile(r"^(`{3,})\S*\s*$")
INDENTED_GHERKIN_RE = re.compile(r"^\s+`{3,}gherkin\s*$")
RULE_RE = re.compile(r"^\s*Rule:\s*(.+)$")
SCENARIO_RE = re.compile(r"^\s*Scenario(?: Outline)?:\s*(.+)$")
MARKER_RE = re.compile(r"@openspec:\s*(ADDED|MODIFIED|REMOVED|RENAMED)")
AC_RE = re.compile(r"<!--\s*AC:\s*([^\s]+)\s*-->")
AC_FULL_RE = re.compile(r"<!--\s*AC:\s*([^\s#]+)#(\d+)\s*-->")
TICKET_RE = re.compile(r"^\s*-\s*\*\*Ticket:\*\*\s*(.+?)\s*$")
AC_HEADING_RE = re.compile(r"^\s*-\s*\*\*Acceptance Criteria:\*\*\s*$")
AC_LINE_RE = re.compile(r"^\s*(\d+)\.\s")


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


def extract_all(openspec_dir, out_dir):
    here = Path(__file__).resolve().parent
    openspec_dir = Path(openspec_dir).resolve() if openspec_dir else here / ".."
    out_dir = Path(out_dir).resolve() if out_dir else here / ".tmp-validate"

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


def spec_sources(openspec_dir):
    """All spec.md files (source of truth + active change deltas), archive excluded."""
    openspec_dir = Path(openspec_dir)
    return sorted(
        openspec_dir / p
        for p in collect_spec_sources(openspec_dir, "spec.md")
    )


def is_delta(spec_path, openspec_dir):
    """True when the spec lives under a change's specs/ (a delta, not source of truth)."""
    return "changes/" in spec_path.relative_to(openspec_dir).as_posix()


def check_gherkin_syntax(spec_path):
    """Extract; return error string on fence errors, empty gherkin, etc."""
    try:
        extract_file(spec_path)
    except ExtractionError as err:
        return str(err)
    return None


def check_delta_markers(spec_path):
    """A delta spec's Rules must each carry a # @openspec: marker."""
    lines = re.split(r"\r?\n", spec_path.read_text(encoding="utf-8"))
    in_fence = None
    errors = []
    pending_marker = None
    rule_lines = []
    for i, line in enumerate(lines):
        open_m = GHERKIN_OPEN_RE.match(line)
        if open_m and not in_fence:
            in_fence = len(open_m.group(1))
            continue
        if in_fence and re.match(r"^`{%d,}\s*$" % in_fence, line):
            in_fence = None
            continue
        if not in_fence:
            continue
        marker = MARKER_RE.search(line)
        if marker:
            pending_marker = marker.group(1)
            continue
        rule = RULE_RE.match(line)
        if rule:
            rule_lines.append((i + 1, rule.group(1).strip(), pending_marker))
            pending_marker = None
    for lineno, name, marker in rule_lines:
        if not marker:
            errors.append(
                '%s:%d: Rule "%s" has no "# @openspec:" operation marker' % (spec_path, lineno, name)
            )
            continue
        if marker in ("ADDED", "MODIFIED") and _scenario_count_after(spec_path, lineno) < 1:
            errors.append(
                '%s:%d: Rule "%s" marked %s must have at least one Scenario' % (spec_path, lineno, name, marker)
            )
    return errors


def _scenario_count_after(spec_path, rule_lineno):
    """Count Scenario/Scenario Outline lines between a Rule and the next Rule or fence end."""
    lines = spec_path.read_text(encoding="utf-8").split("\n")
    count = 0
    for line in lines[rule_lineno:]:
        if RULE_RE.match(line):
            break
        if SCENARIO_RE.match(line):
            count += 1
    return count


def check_ac_traceability(spec_path):
    """Each AC comment must be followed (in this file) by at least one scenario."""
    lines = re.split(r"\r?\n", spec_path.read_text(encoding="utf-8"))
    total_ac = sum(1 for line in lines if AC_RE.search(line))
    total_scenarios = sum(1 for line in lines if SCENARIO_RE.match(line))
    if total_ac and total_scenarios < total_ac:
        return [
            "%s: %d Jira AC comment(s) but only %d scenario(s); every AC must map to at least one scenario"
            % (spec_path, total_ac, total_scenarios)
        ]
    return []


def _source_ac_numbers(proposal_path):
    """Return (ticket_id, {ac_number: line_number}) from a proposal's ## Source section.

    The ticket id is the `**Ticket:**` value (stripped of an HTML comment
    placeholder); AC numbers come from the numbered lines under the
    `**Acceptance Criteria:**` heading. Returns (None, {}) when the proposal
    has no ticket or no AC list (e.g. a tooling change without a ticket).
    """
    lines = re.split(r"\r?\n", proposal_path.read_text(encoding="utf-8"))
    ticket = None
    in_ac = False
    acs = {}
    for i, line in enumerate(lines):
        t = TICKET_RE.match(line)
        if t:
            ticket = t.group(1).strip()
            m = re.search(r"<!--\s*([^>]+?)\s*-->", ticket)
            if m:
                ticket = m.group(1).strip()
            continue
        if AC_HEADING_RE.match(line):
            in_ac = True
            continue
        if in_ac:
            if re.match(r"^##\s", line):
                break
            m = AC_LINE_RE.match(line)
            if m:
                acs[int(m.group(1))] = i + 1
    return ticket, acs


def check_ac_coverage(openspec_dir, change_dir):
    """Coverage gate for one active change with specs.

    Every AC listed in the change's proposal `## Source` must map to an
    `<!-- AC: TICKET-ID#N -->` comment in the change's spec files, and every
    such comment must reference an AC that exists in `## Source` (no orphans).
    """
    proposal_path = change_dir / "proposal.md"
    if not proposal_path.exists():
        return []
    ticket, acs = _source_ac_numbers(proposal_path)
    if not ticket or not acs:
        return []

    change_specs = sorted(
        p for p in (change_dir / "specs").rglob("spec.md") if "changes/archive/" not in p.as_posix()
    )
    if not change_specs:
        return []

    referenced = {}  # ac_number -> list of spec files
    for spec_path in change_specs:
        lines = re.split(r"\r?\n", spec_path.read_text(encoding="utf-8"))
        for line in lines:
            m = AC_FULL_RE.search(line)
            if m and m.group(1) == ticket:
                referenced.setdefault(int(m.group(2)), []).append(spec_path.name)

    issues = []
    for ac_num in sorted(acs):
        if ac_num not in referenced:
            issues.append(
                "%s:%d: AC %s#%d listed in ## Source has no <!-- AC: %s#%d --> comment in the change's specs"
                % (proposal_path, acs[ac_num], ticket, ac_num, ticket, ac_num)
            )
    for ac_num, files in sorted(referenced.items()):
        if ac_num not in acs:
            issues.append(
                "AC comment %s#%d in %s has no matching AC in ## Source (orphan)"
                % (ticket, ac_num, ", ".join(sorted(set(files))))
            )
    return issues


def _provision_lintrc(cwd):
    """Point gherkin-lint at a `.gherkin-lintrc`, provisioning one if absent.

    The rc is only copied to the repository root when a jira-driven validation
    workflow is invoked (this script) or the acceptance-test-authoring skill has
    scaffolded `acceptance-tests/`; it is not kept in the schema directory.
    Sources, in order: an existing root `.gherkin-lintrc`, the acceptance-test
    pack's copy, then the skill reference. Returns the rc path or None.
    """
    candidate = cwd / ".gherkin-lintrc"
    if candidate.exists():
        return candidate
    sources = [
        cwd / "acceptance-tests" / ".gherkin-lintrc",
        cwd / ".agents" / "skills" / "acceptance-test-authoring" / "references" / "gherkin-lintrc.json",
    ]
    for src in sources:
        if src.exists():
            shutil.copy2(src, candidate)
            sys.stderr.write("[validate] provisioned .gherkin-lintrc from %s\n" % src)
            return candidate
    return None


def run_gherkin_lint(cwd, extracted_dir):
    """Run npx gherkin-lint over the extracted directory; returns (exit, output).

    gherkin-lint locates `.gherkin-lintrc` relative to the working directory, so
    the script first provisions one into the working directory (from the
    acceptance-tests copy or the skill reference) and runs with cwd there.
    Returns (None, error) if no config source is available.
    """
    rc = _provision_lintrc(cwd)
    if rc is None:
        sys.stderr.write(
            "[validate] skipping gherkin-lint: no .gherkin-lintrc and no source to provision from\n"
        )
        return None, ""
    proc = subprocess.run(
        ["npx", "gherkin-lint", str(extracted_dir)],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main(argv):
    here = Path(__file__).resolve().parent
    cwd = Path.cwd()
    openspec_dir = Path(argv[0]).resolve() if argv else (cwd / "openspec").resolve()
    extracted_dir = Path(argv[1]).resolve() if len(argv) > 1 else (here / ".tmp-validate").resolve()

    spec_files = spec_sources(openspec_dir)
    if not spec_files:
        sys.stderr.write("[validate] no spec.md files found under %s; nothing to validate\n" % openspec_dir)
        return 0

    all_issues = []
    extraction_failed = False
    for spec_path in spec_files:
        err = check_gherkin_syntax(spec_path)
        if err:
            all_issues.append(err)
            extraction_failed = True
            continue
        if is_delta(spec_path, openspec_dir):
            all_issues.extend(check_delta_markers(spec_path))
        all_issues.extend(check_ac_traceability(spec_path))

    changes_dir = openspec_dir / "changes"
    if changes_dir.is_dir():
        for entry in sorted(changes_dir.iterdir()):
            if not entry.is_dir() or entry.name == "archive":
                continue
            all_issues.extend(check_ac_coverage(openspec_dir, entry))

    if not extraction_failed:
        extracted_dir.mkdir(parents=True, exist_ok=True)
        try:
            extract_all(openspec_dir, extracted_dir)
        except ExtractionError as err:
            all_issues.append(str(err))

    if not all_issues:
        lint_code, lint_out = run_gherkin_lint(cwd, extracted_dir)
        if lint_code is not None and lint_code != 0:
            all_issues.append("gherkin-lint failed:\n" + lint_out)
        elif lint_code == 0:
            sys.stderr.write("[validate] gherkin-lint: ok\n")
        # lint_code is None when no .gherkin-lintrc exists — handled by the skips message above.

    return _report(all_issues)


def _report(issues):
    if not issues:
        sys.stderr.write("[validate] ok\n")
        return 0
    sys.stderr.write("[validate] %d issue(s):\n" % len(issues))
    for issue in issues:
        for line in issue.split("\n"):
            sys.stderr.write("  " + line + "\n")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))