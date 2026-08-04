---
name: bdd-zone-check
description: Spec-first discipline and specs/code zone isolation — every code change must be driven by an active spec change, and a unit of work touches either openspec/ (specs) or code, never both (tasks.md exempt). Use when starting to implement any feature or fix, before writing or editing code, when acceptance tests fail, when code changes exist without a corresponding spec change, when the zone guard denies an edit, when planning a task that spans both specs and code, or when switching between spec work and code work.
---

# BDD zone check (spec-first + specs/code isolation)

This repo enforces two disciplines:

1. **Spec-first.** Code is only ever written to implement an active spec change (a delta under `openspec/changes/`). Code without a driving spec change is invalid, even if all tests pass.
2. **Zone isolation.** A unit of work touches either `openspec/` (the **specs** zone) or the rest of the repo (the **code** zone) — never both. The zone is tied to **git state**, not to a session: whatever uncommitted changes exist define the active zone, and committing (or stashing) releases it.

## The rules

1. **Directional blocking (live).** If uncommitted changes (staged, unstaged, or untracked) exist in one zone, edits to the other zone are denied. Commit or stash the pending work to switch zones — no new session needed.
2. **No mixed commits.** Never commit `openspec/` files and code files together — commit each zone separately.
3. **Exemption.** Any file named `tasks.md` is ignored by every check — it may be edited and committed alongside either zone.

## Code without a spec: revert and restart

If code changes exist that were not driven by an active spec change — especially when acceptance tests are failing — the only correct response is to throw the code away and start from the spec. Patching unspecced code until tests pass is a rule violation, not a fix.

1. **Detect**: uncommitted code-zone changes with no active change under `openspec/changes/` whose scenarios describe them.
2. **Revert all code changes**: `git restore .` for tracked files plus `git clean -fd` for untracked ones (or `git stash` and drop it).
3. **Start from the spec**: create or update the spec delta (proposal + Gherkin scenarios) that defines the intended behavior, and commit it.
4. **Re-implement** from the now-committed spec, keeping the acceptance suite green.

## How it is enforced (skills cannot enforce — the hook does)

This skill is guidance only. Live enforcement is the consuming project's responsibility: a zone-guard hook that fires before every file edit (in Claude Code, a `PreToolUse` hook on `Edit|Write|NotebookEdit`, wired in `.claude/settings.json`). It runs `git status --porcelain`, classifies pending changes into zones, and denies the edit if the target file's zone conflicts with the dirty zone. Files outside the repo are ignored.

A reference implementation (`.claude/hooks/zone-guard.sh`) ships with the behavior-driven-template project.

## When you are blocked

- **Edit denied ("uncommitted X changes exist")**: finish the current zone's task, run the project's test suite if code changed, then commit that work. After the tree is clean, edit the other zone. If the pending work is not ready to commit, `git stash` it instead.
- **Tree already mixes zones** (e.g. changes made outside Claude): the guard denies all non-exempt edits until you commit or stash one side.

## Checking manually

- Which zone is active: `git status --porcelain` — any non-`tasks.md` path under `openspec/` means specs, anything else means code.
- Is there an active spec change driving the code work: look for an unarchived change under `openspec/changes/`.
