# pnpm Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace npm with pnpm for the Vue frontend and update the docs so the frontend is started and built with a single package manager.

**Architecture:** Keep the change isolated to `web/` tooling and project documentation. The app code does not change; only the package manager, lockfile, and command references do. Verification runs the same web tests and build through pnpm so the new workflow is exercised end-to-end.

**Tech Stack:** pnpm, Vite, Vue 3, Vitest, TypeScript

## Global Constraints

- Replace npm with pnpm for the Vue frontend.
- Update docs and setup instructions wherever they mention `npm install`, `npm run dev`, `npm run build`, or `npm test`.
- Keep the Python backend unchanged.
- Preserve the existing frontend behavior and test coverage.

---

### Task 1: Switch Web Tooling to pnpm

**Files:**
- Modify: `web/package.json`
- Delete: `web/package-lock.json`
- Create: `web/pnpm-lock.yaml`

**Interfaces:**
- Consumes: existing frontend scripts in `web/package.json`
- Produces: `pnpm` workflow for install, dev, test, and build

- [ ] **Step 1: Run the install to generate the pnpm lockfile**

Run: `pnpm install`

Expected: `web/pnpm-lock.yaml` is created and `web/package-lock.json` is no longer needed.

- [ ] **Step 2: Verify the web test command runs through pnpm**

Run: `pnpm test -- --run src/components/__tests__/DashboardPanels.spec.ts src/components/__tests__/DashboardFilterBar.spec.ts src/components/__tests__/DashboardPage.spec.ts`

Expected: all selected Vitest suites pass.

- [ ] **Step 3: Verify the production build runs through pnpm**

Run: `pnpm build`

Expected: Vite build completes successfully.

### Task 2: Update Documentation and Command References

**Files:**
- Modify: `readme.md`
- Modify: `docs/architecture/frontend-transition.md`
- Modify: `docs/superpowers/plans/2026-07-03-vue-dashboard.md`

**Interfaces:**
- Consumes: the pnpm commands validated in Task 1
- Produces: docs that point contributors at `pnpm install`, `pnpm dev`, `pnpm build`, and `pnpm test`

- [ ] **Step 1: Replace npm command snippets with pnpm equivalents**

Use these replacements:

```text
npm install -> pnpm install
npm run dev -> pnpm dev
npm run build -> pnpm build
npm test -> pnpm test
```

- [ ] **Step 2: Re-read the edited docs for consistency**

Run: `python3 - <<'PY'
from pathlib import Path
for path in [Path('readme.md'), Path('docs/architecture/frontend-transition.md'), Path('docs/superpowers/plans/2026-07-03-vue-dashboard.md')]:
    text = path.read_text()
    assert 'npm install' not in text
    assert 'npm run dev' not in text
    assert 'npm run build' not in text
    assert 'npm test' not in text
print('docs ok')
PY`

Expected: the script prints `docs ok`.

### Task 3: Final Verification

**Files:**
- None

**Interfaces:**
- Consumes: the pnpm workflow and updated docs
- Produces: a clean web build and repo status with pnpm lockfile in place

- [ ] **Step 1: Run the focused frontend checks again**

Run: `pnpm test -- --run src/components/__tests__/DashboardPanels.spec.ts src/components/__tests__/DashboardFilterBar.spec.ts src/components/__tests__/DashboardPage.spec.ts && pnpm build`

Expected: all tests pass and the build succeeds.

- [ ] **Step 2: Confirm the lockfile migration**

Run: `git status --short`

Expected: `web/pnpm-lock.yaml` is present and `web/package-lock.json` is removed.
