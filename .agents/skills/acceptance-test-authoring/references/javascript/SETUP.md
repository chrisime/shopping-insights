# JavaScript stack — cucumber-js

For `stack: javascript` in `openspec/config.yaml`. Read the skill's SKILL.md first: it holds the spec format, the invariants and the effective-spec procedure this pack implements.

## Files to copy

Copy into `acceptance-tests/` at the repo root. **Destination filenames are load-bearing** — the reasons are not stylistic:

| Source | Destination | Why the name is fixed |
|---|---|---|
| `javascript/extract-gherkin.cjs` | `extract-gherkin.cjs` | `cucumber.cjs` requires it as `./extract-gherkin.cjs` |
| `javascript/cucumber.cjs` | `cucumber.cjs` | cucumber-js discovers its configuration by this exact name |
| `javascript/openspec-effective-paths.cjs` | `openspec-effective-paths.cjs` | required by `cucumber.cjs` under this name |
| `../gherkin-lintrc.json` | `.gherkin-lintrc` | gherkin-lint auto-discovers this name and has no built-in defaults |

Note the fourth is from the shared `references/` root, not this folder — one linter serves both stacks.

## Project setup

`acceptance-tests/` is an independent Node project with its own `package.json`. Its hooks boot the application before the suite and shut it down after, so the suite runs with a single command.

devDependencies: `@cucumber/cucumber`, `glob`, `cheerio`, `gherkin-lint`.

```json
"scripts": {
  "test": "cucumber-js",
  "test:specs": "cucumber-js -p specs",
  "lint:specs": "node extract-gherkin.cjs && gherkin-lint .extracted"
}
```

`npm test` stays a plain `cucumber-js` call: `cucumber.cjs` runs `extractAll()` synchronously at config load, so both profiles always see a freshly rebuilt `.extracted/`. No wrapper script is needed — this is the one structural advantage the JS stack has over the Python one.

## How exclusion works here

cucumber-js filters at **discovery** time via line-targeted paths (`spec.feature:27:33` loads only the scenarios starting at those lines), so superseded scenarios are never loaded and never appear as skipped. `effectivePaths()` computes these paths; nothing is written back to `.extracted/`.

**Never use negated (`!`) globs to exclude the archive** — cucumber-js does not support negation in `paths` and silently ignores such patterns, so the exclusion looks configured but does nothing. Use include-only patterns plus the explicit `changes/archive/` filter, as the reference files do.

## Verification

```sh
npx cucumber-js --dry-run                                    # scenario count
node -e "console.log(require('./cucumber.cjs').default.paths)"   # resolved paths
```

Resolved paths must show only `.extracted/` entries, some line-targeted, and nothing under `changes/archive/`.

For a name-level parity diff against another stack, read **`testCase` envelopes, not `pickle` envelopes** — `-f message` emits a `pickle` for every pickle in a loaded file, including the line-excluded ones, so counting pickles overreports:

```sh
npx cucumber-js --dry-run -f message | \
  node -e "let p={},s=[];require('readline').createInterface({input:process.stdin}).on('line',l=>{try{const m=JSON.parse(l);if(m.pickle)p[m.pickle.id]=m.pickle.name;if(m.testCase)s.push(m.testCase.pickleId)}catch{}}).on('close',()=>console.log(s.map(i=>p[i]).sort().join('\n')))"
```

## Linting

Pass `.extracted` as a **directory argument** — a quoted `'**'` glob silently matches nothing through the dot-directory. Reported line numbers are valid in the source `spec.md`.

Known limitation: gherkin-lint's AST rules do not descend into `Rule:` children, so e.g. `no-unnamed-scenarios` misses scenarios nested under a Rule. Line-based rules (trailing spaces, tags) and feature-level rules work fine. This limitation applies to both stacks, since both use gherkin-lint — which is the point: the two stacks accept and reject exactly the same specs.

## Page Object Model

Page objects live in `acceptance-tests/support/pages/`, one per screen or flow (`signup-page.js`, `login-page.js`). Parse responses with **cheerio** — never with regexes over raw HTML. The World stays a thin HTTP client holding page-object instances.

```js
When('they submit a valid email and password', async function () {
  this.result = await this.signupPage.submitSignup({
    email: 'user@example.com',
    password: 'correct-horse-battery-staple',
  });
});

Then('an error message is shown', function () {
  assert.ok(this.signupPage.errorMessage());
});
```
