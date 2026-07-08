# KPI Card Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align first field left, second field right inside each KPI card in DashboardKpiGrid.

**Architecture:** Single file change — replace `rightAlignFields` Set lookup with index-based alignment in the `v-for` loop.

**Tech Stack:** Vue 3, Tailwind CSS

## Global Constraints

- No new dependencies
- 38 frontend tests must pass after change
- `corepack pnpm build` must pass
- Follow existing code style (no comments, no emoji)

---

### Task 1: Index-based alignment in DashboardKpiGrid

**Files:**
- Modify: `web/src/components/DashboardKpiGrid.vue:46` (remove `rightAlignFields` Set)
- Modify: `web/src/components/DashboardKpiGrid.vue:112-117` (change alignment class)

- [ ] **Step 1: Remove `rightAlignFields` and update template**

Remove lines 46:
```
const rightAlignFields = new Set(["rewe_discount_pct", "lidlplus_discount_pct", "sticker_discount_pct", "lidl_discount_pct", "rewe_bonus_balance", "rewe_bonus_open", "total_savings_pct"]);
```

Change the `v-for` to use index and apply right alignment on the second field (`fi === 1`):

```diff
-          <div
-            v-for="field in card.fields"
-            :key="field"
-            class="grid gap-1"
-            :class="rightAlignFields.has(field) ? 'justify-items-end text-right' : ''"
-          >
+          <div
+            v-for="(field, fi) in card.fields"
+            :key="field"
+            class="grid gap-1"
+            :class="fi === 1 ? 'justify-items-end text-right' : ''"
+          >
```

- [ ] **Step 2: Run frontend tests**

```bash
corepack pnpm test -- --run
```
Expected: 38 passed, 0 failed

- [ ] **Step 3: Run frontend build**

```bash
corepack pnpm build
```
Expected: build succeeds

- [ ] **Step 4: Commit**

```bash
git add web/src/components/DashboardKpiGrid.vue
git commit -m "feat: align KPI card fields by index — first left, second right"
```
