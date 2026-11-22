---
name: bdd-zone-check
description: Use when starting to implement any feature or fix, before writing or editing code, when acceptance tests fail, when code changes exist without a corresponding spec change, when planning work that spans both specs and code, or when switching between spec work and code work.
---

# BDD Zone Check

This repo uses two behavior-driven disciplines:

1. **Spec-first.** Code is only written to implement an active spec change under `openspec/changes/`. Code without a driving spec change is invalid, even if all tests pass.
2. **Zone isolation.** A unit of work touches either `openspec/` (the specs zone) or the rest of the repo (the code zone), never both. The zone is tied to git state: uncommitted changes define the active zone, and committing or stashing releases it.

## Rules

1. If uncommitted changes exist in one zone, finish, commit, or stash them before editing the other zone.
2. Never commit `openspec/` files and code files together.
3. Any file named `tasks.md` is exempt and may be edited with either zone.

## Code Without A Spec

If code changes exist that were not driven by an active spec change, especially when acceptance tests are failing, the correct response is to discard the code and restart from the spec. Patching unspecced code until tests pass is a rule violation, not a fix.

1. Detect uncommitted code-zone changes with no active change under `openspec/changes/` whose scenarios describe them.
2. Revert or stash the code changes. Do not modify user-owned work without explicit permission.
3. Create or update the spec delta with proposal and scenarios (fenced Gherkin for every schema here - `intent-driven`, `behaviour-driven`, and `jira-driven` all author ` ```gherkin ` fences; see `openspec/config.yaml` for the active schema).
4. Commit the spec-zone work.
5. Re-implement from the committed spec, keeping the acceptance suite green.

## OpenCode Note

This skill is guidance only. The source behavior-driven template enforces zone isolation with Claude Code hooks, but those hooks are intentionally not copied into this OpenCode template. Until an equivalent OpenCode pre-edit guard is added, manually check git status before crossing zones.

## Manual Checks

- Active zone: `git status --porcelain`. Any non-`tasks.md` path under `openspec/` means specs zone; anything else means code zone.
- Driving spec: look for an unarchived change under `openspec/changes/` whose scenarios describe the code work.
- Zone switch: commit or stash current-zone changes first.
