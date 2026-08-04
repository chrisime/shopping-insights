#!/usr/bin/env python3
"""Composes the EFFECTIVE spec for the behave run: openspec/specs (source of
truth) with every active change's delta applied -- i.e. what openspec/specs
will become once the active changes are synced/archived.

Specs are authored as spec.md (Markdown with ```gherkin fences); this module
operates on the .feature files that extract_gherkin.py writes to .extracted/,
which mirror the openspec/ tree. Extraction preserves line numbers exactly
(prose becomes blank lines), so every line number below -- and the composition
report -- is also valid in the source spec.md. The report prints spec.md paths
for that reason.

Composition rules, per Rule in an active delta:
  ADDED     -> runs from the delta file
  MODIFIED  -> delta version runs; the source-of-truth version is superseded
  REMOVED   -> the source-of-truth version is superseded
  RENAMED   -> name change only; source-of-truth scenarios keep running

HOW SUPERSEDED RULES ARE EXCLUDED -- AND WHY THIS DIFFERS FROM THE JS STACK
--------------------------------------------------------------------------
The contract (skill runner invariant 3) is that a superseded scenario must not
reach the runner AND must not show up as "skipped": a skipped count pollutes
the zero-pending completion signal, because a superseded rule is replaced, not
unfinished.

cucumber-js satisfies this with line-targeted paths (`spec.feature:12:19`),
which filter at DISCOVERY time -- the other scenarios are never loaded.

behave's equivalent (`spec.feature:12`) does NOT: it selects at runtime and
reports every unselected scenario as skipped ("2 passed, 1 skipped"). Neither
`show_skipped = false` nor `--no-skipped` suppresses that count; they only
affect printing. So line targeting cannot satisfy the contract here.

Instead this module PRUNES the superseded Rule blocks out of the extracted
tree, blanking their lines in place, and hands behave whole files. That is not
a spec edit: .extracted/ is a generated artifact -- gitignored, wiped and
rebuilt on every run -- so the source of truth stays pristine until sync, which
is what the invariant actually protects. Blanking (rather than deleting) lines
keeps the line-fidelity invariant intact, so the surviving scenarios still sit
at their original spec.md line numbers.

Parsing is line-based, using the same regexes as
openspec/schemas/behavior-driven/schema.yaml `format:`. A literal "Rule:" at
the start of a docstring line inside a gherkin fence would be miscounted; none
exist here. (Markdown prose is already blanked by extraction, so prose
mentioning "Rule:" is harmless.)

Stdlib only, 3.8+ compatible. See the skill's "Port parity" note before
changing this or its JS peer, javascript/openspec-effective-paths.cjs.
"""

import re
import sys
from pathlib import Path

RULE_RE = re.compile(r"^\s*Rule:\s*(.+)$")
MARKER_RE = re.compile(r"@openspec:\s*(ADDED|MODIFIED|REMOVED|RENAMED)")
SCENARIO_RE = re.compile(r"^\s*Scenario(?: Outline)?:\s*(.*)$")

HERE = Path(__file__).resolve().parent


class CompositionError(Exception):
    """Two active changes supersede the same rule -- unresolvable composition."""


def _read_lines(feature_path):
    return re.split(r"\r?\n", (HERE / feature_path).read_text(encoding="utf-8"))


def _source_of(feature_path):
    """Maps an extracted path back to the spec.md it came from, for reporting.
    Same line numbers apply (extraction preserves them)."""
    out = re.sub(r"^\.extracted/", "../openspec/", str(feature_path))
    return re.sub(r"spec\.feature$", "spec.md", out)


def _capability_of(feature_path):
    """Both '.extracted/specs/<capability>/...' and
    '.extracted/changes/<id>/specs/<capability>/...' name the capability right
    after their last 'specs' segment."""
    parts = str(feature_path).split("/")
    return parts[len(parts) - 1 - parts[::-1].index("specs") + 1]


def _change_id_of(delta_path):
    parts = str(delta_path).split("/")
    return parts[parts.index("changes") + 1]


def collect_superseded_rules(delta_paths):
    """-> {capability: {rule_name: change_id}} for rules whose source-of-truth
    version is superseded by an active delta (MODIFIED or REMOVED)."""
    superseded = {}
    for delta_path in delta_paths:
        capability = _capability_of(delta_path)
        change_id = _change_id_of(delta_path)
        pending_op = None  # marker applies to the next Rule: line
        for line in _read_lines(delta_path):
            marker = MARKER_RE.search(line)
            if marker:
                pending_op = marker.group(1)
                continue
            rule = RULE_RE.match(line)
            if not rule:
                continue
            name = rule.group(1).strip()
            if pending_op in ("MODIFIED", "REMOVED"):
                by_rule = superseded.setdefault(capability, {})
                other_change = by_rule.get(name)
                if other_change and other_change != change_id:
                    raise CompositionError(
                        'Active changes "%s" and "%s" both supersede rule "%s" of '
                        'capability "%s". Resolve the conflict (merge or sequence '
                        "the changes) before running the suite."
                        % (other_change, change_id, name, capability)
                    )
                by_rule[name] = change_id
            pending_op = None
    return superseded


def _rule_blocks(lines):
    """-> [(rule_name, start_idx, end_idx_exclusive)]. A Rule owns every line
    from its own down to the line before the next Rule (or EOF)."""
    starts = [(i, m.group(1).strip()) for i, m in
              ((i, RULE_RE.match(line)) for i, line in enumerate(lines)) if m]
    blocks = []
    for pos, (idx, name) in enumerate(starts):
        end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
        blocks.append((name, idx, end))
    return blocks


def prune_source_of_truth_spec(spec_path, superseded_by_rule):
    """Blanks the superseded Rule blocks of one extracted source-of-truth file,
    in place. -> (kept_scenario_count, seen_rules, excluded).

    `excluded` lists each superseded rule with the change that superseded it and
    the scenarios left out of the run (name + 1-based spec.md line)."""
    lines = _read_lines(spec_path)
    seen_rules = set()
    excluded = []
    blanked = set()

    for name, start, end in _rule_blocks(lines):
        seen_rules.add(name)
        if name not in superseded_by_rule:
            continue
        entry = {"rule": name, "change_id": superseded_by_rule[name], "scenarios": []}
        for idx in range(start, end):
            scenario = SCENARIO_RE.match(lines[idx])
            if scenario:
                entry["scenarios"].append(
                    {"name": scenario.group(1).strip() or "(unnamed scenario)", "line": idx + 1}
                )
            blanked.add(idx)
        excluded.append(entry)

    if not excluded:
        kept = sum(1 for line in lines if SCENARIO_RE.match(line))
        return kept, seen_rules, excluded

    pruned = ["" if i in blanked else line for i, line in enumerate(lines)]
    if len(pruned) != len(lines):
        raise CompositionError("%s: line-count invariant violated (pruning bug)" % spec_path)
    (HERE / spec_path).write_text("\n".join(pruned), encoding="utf-8")

    kept = sum(1 for line in pruned if SCENARIO_RE.match(line))
    return kept, seen_rules, excluded


def _print_composition_report(exclusions):
    """Composition report: every scenario left out of the run, and why. Printed
    to stderr only when an active change supersedes something -- an excluded
    scenario must never be silently absent from results and reports. Paths are
    the source spec.md files (line numbers identical to the extracted files)."""
    left_out = 0
    for spec_path, capability, rules in exclusions:
        for entry in rules:
            sys.stderr.write("[effective-spec] %s / Rule: %s\n" % (capability, entry["rule"]))
            sys.stderr.write("[effective-spec]   superseded by change: %s\n" % entry["change_id"])
            for scenario in entry["scenarios"]:
                sys.stderr.write(
                    "[effective-spec]   left out: %s (%s:%d)\n"
                    % (scenario["name"], _source_of(spec_path), scenario["line"])
                )
                left_out += 1
    sys.stderr.write(
        "[effective-spec] %d source-of-truth scenario(s) excluded; "
        "delta versions run from openspec/changes/\n" % left_out
    )


def _rel(path):
    return path.relative_to(HERE).as_posix()


def effective_locations():
    """Prunes the extracted tree and returns the behave locations for the
    effective spec: surviving source-of-truth files + every active delta file."""
    # Archived changes are historical deltas; they must never execute.
    # Extraction already skips the archive; the filter here is defense in depth.
    delta_paths = sorted(
        _rel(p) for p in (HERE / ".extracted" / "changes").glob("*/specs/**/*.feature")
        if "changes/archive/" not in _rel(p)
    )
    sot_paths = sorted(_rel(p) for p in (HERE / ".extracted" / "specs").glob("**/*.feature"))

    superseded = collect_superseded_rules(delta_paths)

    locations = []
    seen_rules_by_capability = {}
    exclusions = []
    for spec_path in sot_paths:
        capability = _capability_of(spec_path)
        superseded_by_rule = superseded.get(capability)
        if not superseded_by_rule:
            locations.append(spec_path)
            continue
        kept, seen_rules, excluded = prune_source_of_truth_spec(spec_path, superseded_by_rule)
        # Omit the file entirely when nothing survives -- an all-superseded
        # capability must not reach behave as an empty feature.
        if kept > 0:
            locations.append(spec_path)
        seen_rules_by_capability[capability] = seen_rules
        if excluded:
            exclusions.append((spec_path, capability, excluded))

    if exclusions:
        _print_composition_report(exclusions)

    # Delta drift: a MODIFIED/REMOVED rule should exist in the source of truth.
    for capability, by_rule in superseded.items():
        seen_rules = seen_rules_by_capability.get(capability, set())
        for name, change_id in by_rule.items():
            if name not in seen_rules:
                sys.stderr.write(
                    '[effective-spec] WARNING: change "%s" marks rule "%s" of '
                    'capability "%s" as MODIFIED/REMOVED, but no such rule exists '
                    "in openspec/specs -- delta may have drifted from the source "
                    "of truth.\n" % (change_id, name, capability)
                )

    return locations + delta_paths


def source_of_truth_locations():
    """The `--specs` regression run: source of truth only, as-is, unpruned."""
    return sorted(_rel(p) for p in (HERE / ".extracted" / "specs").glob("**/*.feature"))
