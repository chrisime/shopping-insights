'use strict';

// Computes the cucumber `paths` for the EFFECTIVE spec: openspec/specs
// (source of truth) with every active change's delta applied — i.e. what
// openspec/specs will become once the active changes are synced/archived.
//
// Specs are authored as spec.md (Markdown with ```gherkin fences); this
// module operates on the .feature files that extract-gherkin.cjs writes to
// .extracted/, which mirror the openspec/ tree. Extraction preserves line
// numbers exactly (prose becomes blank lines), so every line number below —
// line-targeted cucumber paths and the composition report — is also valid in
// the source spec.md. The report prints spec.md paths for that reason;
// cucumber `paths` keep the .extracted form.
//
// Composition rules, per Rule in an active delta:
//   ADDED     -> runs from the delta file
//   MODIFIED  -> delta version runs; the source-of-truth version is superseded
//   REMOVED   -> the source-of-truth version is superseded
//   RENAMED   -> name change only; source-of-truth scenarios keep running
//
// Superseded rules are excluded at DISCOVERY time via cucumber line targeting
// (`file.feature:12:19` runs only the scenarios starting at those lines).
// Spec files are never edited, tagged, or runtime-skipped: the source of
// truth stays pristine until sync, and the suite reports no noise. Green here
// is the gate for sync/archive — and sync/archive must not change results.
//
// Parsing is line-based, using the same regexes as
// openspec/schemas/behavior-driven/schema.yaml `format:`. A literal "Rule:"
// at the start of a docstring line inside a gherkin fence would be
// miscounted; none exist here. (Markdown prose is already blanked by
// extraction, so prose mentioning "Rule:" is harmless.)

const fs = require('node:fs');
const path = require('node:path');
const { globSync } = require('glob');

const RULE_RE = /^\s*Rule:\s*(.+)$/;
const MARKER_RE = /@openspec:\s*(ADDED|MODIFIED|REMOVED|RENAMED)/;
const SCENARIO_RE = /^\s*Scenario(?: Outline)?:\s*(.*)$/;

function readLines(featurePath) {
  return fs
    .readFileSync(path.resolve(__dirname, featurePath), 'utf8')
    .split(/\r?\n/);
}

// Maps an extracted path back to the spec.md it came from, for reporting.
// Same line numbers apply (extraction preserves them).
function sourceOf(featurePath) {
  return featurePath
    .replace(/^\.extracted\//, '../openspec/')
    .replace(/spec\.feature$/, 'spec.md');
}

// Both '.extracted/specs/<capability>/…' and
// '.extracted/changes/<id>/specs/<capability>/…' name the capability right
// after their last 'specs' segment.
function capabilityOf(featurePath) {
  const parts = featurePath.split('/');
  return parts[parts.lastIndexOf('specs') + 1];
}

function changeIdOf(deltaPath) {
  const parts = deltaPath.split('/');
  return parts[parts.indexOf('changes') + 1];
}

// -> Map<capability, Map<ruleName, changeId>> of rules whose source-of-truth
// version is superseded by an active delta (MODIFIED or REMOVED).
function collectSupersededRules(deltaPaths) {
  const superseded = new Map();
  for (const deltaPath of deltaPaths) {
    const capability = capabilityOf(deltaPath);
    const changeId = changeIdOf(deltaPath);
    let pendingOp = null; // marker applies to the next Rule: line
    for (const line of readLines(deltaPath)) {
      const marker = MARKER_RE.exec(line);
      if (marker) {
        pendingOp = marker[1];
        continue;
      }
      const rule = RULE_RE.exec(line);
      if (!rule) continue;
      const name = rule[1].trim();
      if (pendingOp === 'MODIFIED' || pendingOp === 'REMOVED') {
        if (!superseded.has(capability)) superseded.set(capability, new Map());
        const byRule = superseded.get(capability);
        const otherChange = byRule.get(name);
        if (otherChange && otherChange !== changeId) {
          throw new Error(
            `Active changes "${otherChange}" and "${changeId}" both supersede ` +
              `rule "${name}" of capability "${capability}". Resolve the ` +
              `conflict (merge or sequence the changes) before running the suite.`
          );
        }
        byRule.set(name, changeId);
      }
      pendingOp = null;
    }
  }
  return superseded;
}

// -> { entry, seenRules, excluded }: `entry` is the cucumber path for this
// source-of-truth file — the plain path when no rule in it is superseded,
// `file.feature:L1:L2…` keeping only scenarios of surviving rules, or null
// when nothing survives. `excluded` lists each superseded rule with the
// change that superseded it and the scenarios left out of the run.
function filterSourceOfTruthSpec(specPath, supersededByRule) {
  const seenRules = new Set();
  const keptScenarioLines = [];
  const excluded = [];
  let currentExclusion = null;
  readLines(specPath).forEach((line, idx) => {
    const rule = RULE_RE.exec(line);
    if (rule) {
      const name = rule[1].trim();
      seenRules.add(name);
      if (supersededByRule.has(name)) {
        currentExclusion = { rule: name, changeId: supersededByRule.get(name), scenarios: [] };
        excluded.push(currentExclusion);
      } else {
        currentExclusion = null;
      }
      return;
    }
    const scenario = SCENARIO_RE.exec(line);
    if (!scenario) return;
    if (currentExclusion) {
      currentExclusion.scenarios.push({ name: scenario[1].trim() || '(unnamed scenario)', line: idx + 1 });
    } else {
      keptScenarioLines.push(idx + 1);
    }
  });
  if (excluded.length === 0) return { entry: specPath, seenRules, excluded };
  if (keptScenarioLines.length === 0) return { entry: null, seenRules, excluded };
  return { entry: `${specPath}:${keptScenarioLines.join(':')}`, seenRules, excluded };
}

// Composition report: every scenario left out of the run, and why. Printed to
// stderr only when an active change supersedes something — an excluded
// scenario must never be silently absent from results and reports. Paths are
// the source spec.md files (line numbers identical to the extracted files).
function printCompositionReport(exclusions) {
  let leftOut = 0;
  for (const { specPath, capability, rules } of exclusions) {
    for (const { rule, changeId, scenarios } of rules) {
      console.error(`[effective-spec] ${capability} / Rule: ${rule}`);
      console.error(`[effective-spec]   superseded by change: ${changeId}`);
      for (const { name, line } of scenarios) {
        console.error(`[effective-spec]   left out: ${name} (${sourceOf(specPath)}:${line})`);
        leftOut += 1;
      }
    }
  }
  console.error(
    `[effective-spec] ${leftOut} source-of-truth scenario(s) excluded; ` +
      `delta versions run from openspec/changes/`
  );
}

function effectivePaths() {
  // Archived changes are historical deltas; they must never execute.
  // Extraction already skips the archive; the filter here is defense in
  // depth. cucumber-js does NOT support negated (!) globs in `paths`, so
  // exclusion is done structurally (include-only patterns) plus this filter.
  const deltaPaths = globSync('.extracted/changes/*/specs/**/*.feature', {
    cwd: __dirname,
    posix: true,
  }).filter((p) => !p.includes('changes/archive/'));
  const sotPaths = globSync('.extracted/specs/**/*.feature', {
    cwd: __dirname,
    posix: true,
  });

  const superseded = collectSupersededRules(deltaPaths);

  const paths = [];
  const seenRulesByCapability = new Map();
  const exclusions = [];
  for (const specPath of sotPaths) {
    const capability = capabilityOf(specPath);
    const supersededByRule = superseded.get(capability);
    if (!supersededByRule) {
      paths.push(specPath);
      continue;
    }
    const { entry, seenRules, excluded } = filterSourceOfTruthSpec(specPath, supersededByRule);
    if (entry) paths.push(entry);
    seenRulesByCapability.set(capability, seenRules);
    if (excluded.length > 0) exclusions.push({ specPath, capability, rules: excluded });
  }
  if (exclusions.length > 0) printCompositionReport(exclusions);

  // Delta drift: a MODIFIED/REMOVED rule should exist in the source of truth.
  for (const [capability, byRule] of superseded) {
    const seenRules = seenRulesByCapability.get(capability) ?? new Set();
    for (const [name, changeId] of byRule) {
      if (!seenRules.has(name)) {
        console.error(
          `[effective-spec] WARNING: change "${changeId}" marks rule "${name}" ` +
            `of capability "${capability}" as MODIFIED/REMOVED, but no such rule ` +
            `exists in openspec/specs — delta may have drifted from the source of truth.`
        );
      }
    }
  }

  paths.push(...deltaPaths);
  return paths;
}

module.exports = { effectivePaths };
