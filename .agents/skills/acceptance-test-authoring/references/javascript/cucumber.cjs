const { extractAll } = require('./extract-gherkin.cjs');
const { effectivePaths } = require('./openspec-effective-paths.cjs');

// Specs are spec.md files (Markdown with ```gherkin fences) under openspec/.
// Extraction runs synchronously at config load, so BOTH profiles see a fresh
// .extracted/ tree — no wrapper script, `npm test` stays plain `cucumber-js`.
// Line numbers in .extracted/**/spec.feature are identical to the source
// spec.md (prose becomes blank lines).
extractAll();

// Default run = the EFFECTIVE spec: openspec/specs (source of truth) with
// active change deltas applied. Rules marked MODIFIED/REMOVED by an active
// change are superseded — their source-of-truth scenarios are not discovered
// (see openspec-effective-paths.cjs). Archived changes never execute.
const common = {
  paths: effectivePaths(),
  import: ['support/**/*.js', 'step-definitions/**/*.js'],
  format: ['progress-bar', ['html', 'reports/cucumber-report.html']],
};

// `npm run test:specs` — source-of-truth only, an as-is regression run.
const specs = {
  ...common,
  paths: ['.extracted/specs/**/*.feature'],
};

module.exports = { default: common, specs };
