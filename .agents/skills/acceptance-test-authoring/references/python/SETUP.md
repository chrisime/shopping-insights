# Python stack — behave

For `stack: python` in `openspec/config.yaml`. Read the skill's SKILL.md first: it holds the spec format, the invariants and the effective-spec procedure this pack implements.

Requires **behave 1.2.7+** — earlier versions lack Gherkin v6 `Rule:` support, which the whole spec format depends on. Verified against 1.3.3.

## Files to copy

Copy into `acceptance-tests/` at the repo root. **Destination filenames are load-bearing**:

| Source | Destination | Why the name is fixed |
|---|---|---|
| `python/extract_gherkin.py` | `extract_gherkin.py` | imported by `run_acceptance.py` |
| `python/openspec_effective_spec.py` | `openspec_effective_spec.py` | imported by `run_acceptance.py` |
| `python/run_acceptance.py` | `run_acceptance.py` | the documented single entry point |
| `python/behave.ini` | `behave.ini` | behave discovers its config by this name |
| `python/environment.py` | `environment.py` | behave loads hooks from this name, at the base dir |
| `../gherkin-lintrc.json` | `.gherkin-lintrc` | gherkin-lint auto-discovers this name and has no built-in defaults |

Note the last is from the shared `references/` root, not this folder — one linter serves both stacks.

Dependencies: `behave>=1.2.7`, `behave-html-formatter`, plus an HTTP client and HTML parser for the page objects (`requests` + `beautifulsoup4` are the cheerio analogue). `gherkin-lint` is run via `npx`, so it needs no Python install.

## Required layout

```
acceptance-tests/
  run_acceptance.py      environment.py     behave.ini
  extract_gherkin.py     openspec_effective_spec.py
  .gherkin-lintrc
  steps/                 # step definitions
  pages/                 # page objects
  .extracted/  reports/  # generated, gitignored
```

`steps/` and `environment.py` **must sit at the `acceptance-tests/` root**, not under a `features/` directory. behave derives its base directory by walking *up* from the first location argument until it finds a `steps/` directory, and loads `environment.py` from there. With locations like `.extracted/specs/<cap>/spec.feature`, that walk lands on `acceptance-tests/` — which also keeps `.extracted/` and `reports/` at the same paths as the JS stack, so `.gitignore` stays stack-neutral.

## Commands

```sh
python run_acceptance.py                    # the effective spec (default)
python run_acceptance.py --specs            # source of truth only, as-is regression run
python run_acceptance.py --lint             # extract, then gherkin-lint the output
python run_acceptance.py --print-locations  # show the resolved composition
python run_acceptance.py --dry-run          # passthrough; anything unrecognised goes to behave
```

**Always go through the wrapper.** behave parses the feature files *before* `environment.py`'s `before_all` fires, so extraction cannot live in a hook — it would have behave parse a stale `.extracted/` tree and only then rebuild it. `before_all` therefore refuses to start unless the wrapper set `OPENSPEC_ACCEPTANCE`, turning a plain `behave` invocation from a silent wrong-result run into a loud failure. The JS stack needs no such tripwire because its config extracts at load time.

The wrapper runs behave as `sys.executable -m behave`, not the `behave` console script, so an unactivated venv (`.venv/bin/python run_acceptance.py`) still works.

## How exclusion works here — and why it differs from the JS stack

The contract (runner invariant 3) is that a superseded scenario must not reach the runner **and** must not appear as skipped, because a skipped count pollutes the zero-pending completion signal.

cucumber-js meets this with line-targeted paths, which filter at discovery. **behave's `spec.feature:12` does not**: it selects at runtime and reports every unselected scenario as skipped (`2 passed, 1 skipped`). Neither `show_skipped = false` nor `--no-skipped` changes that count — they only affect printing.

So `openspec_effective_spec.py` **prunes** instead: it blanks the superseded `Rule:` blocks out of the extracted tree and hands behave whole files. This is not a spec edit — `.extracted/` is a generated artifact, gitignored and rebuilt every run, so the source of truth stays pristine until sync, which is what the invariant protects. Blanking rather than deleting keeps line fidelity, so surviving scenarios stay at their original `spec.md` line numbers.

`--specs` skips pruning entirely and runs the freshly extracted source of truth as-is.

**One cosmetic artifact:** behave prints a `rules` summary line, and a delta's REMOVED and RENAMED rules legitimately carry no scenarios, so they show there as skipped (`3 rules passed, 2 skipped`). The **scenario** count is the completion signal and stays clean at 0 skipped. cucumber-js prints no rules line, so this is a display difference only.

## Concern mapping vs the JS stack

| Concern | JS | Python |
|---|---|---|
| Extraction trigger | at `cucumber.cjs` config load | explicitly, in `run_acceptance.py` |
| Composition | `effectivePaths()` → line-targeted paths | `effective_locations()` → prune + whole files |
| Runner config | `cucumber.cjs` (executable) | `behave.ini` (static) + wrapper (computed) |
| Profiles | `default` / `specs` | default / `--specs` |
| Stale-run guard | not needed (config always extracts) | `OPENSPEC_ACCEPTANCE` tripwire in `before_all` |

## Verification

```sh
python run_acceptance.py --print-locations   # resolved composition
python run_acceptance.py --dry-run           # scenario count
```

Locations must show only `.extracted/` entries and nothing under `changes/archive/`. Compare the `--dry-run` scenario count and names against the JS stack on the same specs — that cross-stack diff is the strongest guard against the two ports drifting.

## HTML report

`behave.ini` pairs formatters with outfiles **positionally**, so `html` is listed first to claim `reports/behave-report.html` and `progress` gets an explicit `-` for stdout. Do **not** leave an `outfiles` entry blank to mean stdout — behave resolves the empty entry to `.` and dies with `IsADirectoryError`.

Swap in `behave-html-pretty-formatter` by changing the one alias line in `[behave.formatters]`. Avoid allure: `allure-behave` emits only result JSON and needs the separate Java `allure` CLI to produce HTML.

## Page Object Model

Page objects live in `acceptance-tests/pages/`, one per screen or flow (`signup_page.py`, `login_page.py`). Parse responses with **BeautifulSoup** — never with regexes over raw HTML. behave's `context` is the World: a thin HTTP client plus page-object instances, attached in `before_scenario`.

```python
@when('they submit a valid email and password')
def step_impl(context):
    context.result = context.signup_page.submit_signup(
        email='user@example.com',
        password='correct-horse-battery-staple',
    )


@then('an error message is shown')
def step_impl(context):
    assert context.signup_page.error_message()
```
