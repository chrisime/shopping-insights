# Oruga + Tailwind UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Vue dashboard UI with Oruga components for controls and TailwindCSS for layout and visual hierarchy.

**Architecture:** Keep the existing data flow and dashboard payload unchanged. Oruga handles interactive primitives such as form fields and messages, while Tailwind handles the page shell, spacing, surfaces, and responsive layout. The dashboard stays single-page, read-only, and filter-driven.

**Tech Stack:** Vue 3, Vite, TypeScript, Vitest, Vue Test Utils, Oruga Next, TailwindCSS 4

## Global Constraints

- Single-page, desktop-first, balanced analytics view.
- Primarily read-only; filters update content, but no drilldowns or modal flows in the first version.
- CSV export remains out of scope for now.
- OpenAPI hardening / docs polish remains out of scope for now.
- The backend payload must stay section-based (`kind`, `title`, `items`) and must not contain Streamlit-specific formatting.
- The backend payload must be reusable outside Vue.
- The page must remain balanced and not become a dense cockpit UI.

---

### Task 1: Bootstrap Oruga and Tailwind

**Files:**
- Modify: `web/package.json`
- Modify: `web/package-lock.json`
- Modify: `web/vite.config.ts`
- Modify: `web/src/main.ts`
- Create: `web/src/styles.css`
- Create: `web/src/__tests__/main.spec.ts`

**Interfaces:**
- Consumes: Vue app bootstrap from `web/src/main.ts`
- Produces: Oruga plugin registration, Tailwind base styles, and a global stylesheet entrypoint that later components can rely on

- [ ] **Step 1: Write the failing test**

```ts
import { vi, describe, it, expect } from "vitest";

const mountMock = vi.fn();
const useMock = vi.fn(() => ({ mount: mountMock }));

vi.mock("vue", () => ({
  createApp: vi.fn(() => ({ use: useMock })),
}));

vi.mock("../App.vue", () => ({ default: { name: "App" } }));
vi.mock("@oruga-ui/oruga-next", () => ({ default: { name: "OrugaPlugin" } }));

describe("main bootstrap", () => {
  it("registers Oruga and mounts the app", async () => {
    await import("../main");

    expect(useMock).toHaveBeenCalledTimes(1);
    expect(mountMock).toHaveBeenCalledWith("#app");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd web && npm test -- --run src/__tests__/main.spec.ts`

Expected: FAIL because Oruga is not installed/registered yet and `main.ts` does not use the plugin or Tailwind stylesheet yet.

- [ ] **Step 3: Write the minimal implementation**

Install the new UI dependencies first:

```bash
npm install @oruga-ui/oruga-next
npm install -D tailwindcss @tailwindcss/vite
```

```ts
// web/src/main.ts
import { createApp } from "vue";
import Oruga from "@oruga-ui/oruga-next";

import App from "./App.vue";
import "@oruga-ui/oruga-next/dist/oruga.css";
import "./styles.css";

createApp(App).use(Oruga).mount("#app");

// web/src/styles.css
@import "tailwindcss";

html,
body,
#app {
  min-height: 100%;
}

body {
  margin: 0;
  background: #f8fafc;
  color: #0f172a;
  font-family: ui-sans-serif, system-ui, sans-serif;
}

// web/vite.config.ts
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  test: {
    environment: "node",
  },
});
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd web && npm test -- --run src/__tests__/main.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/package.json web/package-lock.json web/vite.config.ts web/src/main.ts web/src/styles.css web/src/__tests__/main.spec.ts
git commit -m "feat: bootstrap oruga and tailwind"
```

---

### Task 2: Restyle the dashboard shell and filters

**Files:**
- Modify: `web/src/components/DashboardPage.vue`
- Modify: `web/src/components/DashboardFilterBar.vue`
- Modify: `web/src/components/DashboardSection.vue`
- Modify: `web/src/App.vue` (only if a root layout wrapper is needed)
- Modify: `web/src/components/__tests__/DashboardPage.spec.ts`
- Create: `web/src/components/__tests__/DashboardFilterBar.spec.ts`

**Interfaces:**
- Consumes: `useDashboard()` state and `DashboardPayload` from `web/src/types/dashboard.ts`
- Produces: a Tailwind-styled dashboard shell with Oruga-powered filters and the same filter-driven refresh behavior

- [ ] **Step 1: Write the failing test**

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import DashboardFilterBar from "../DashboardFilterBar.vue";

describe("DashboardFilterBar", () => {
  it("emits model updates when the user changes a filter", async () => {
    const wrapper = mount(DashboardFilterBar, {
      props: {
        retailer: "",
        startDate: "",
        endDate: "",
        timeGranularity: "Täglich",
        spendingView: "Absolut",
        topView: "Menge",
        topLimit: 20,
      },
    });

    await wrapper.find("select").setValue("lidl");
    expect(wrapper.emitted("update:retailer")?.at(-1)).toEqual(["lidl"]);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd web && npm test -- --run src/components/__tests__/DashboardFilterBar.spec.ts`

Expected: FAIL because the filter bar is still plain HTML/Tailwind and not yet converted to the new Oruga-driven layout.

- [ ] **Step 3: Write the minimal implementation**

```vue
<!-- web/src/components/DashboardFilterBar.vue -->
<template>
  <form class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-3 xl:grid-cols-6" @submit.prevent>
    <o-field label="Händler">
      <o-select v-model="retailer">
        <option value="">Alle</option>
        <option value="lidl">Lidl</option>
        <option value="rewe">REWE</option>
      </o-select>
    </o-field>
    <o-field label="Startdatum">
      <o-input v-model="startDate" type="date" />
    </o-field>
    <o-field label="Enddatum">
      <o-input v-model="endDate" type="date" />
    </o-field>
    <o-field label="Zeitgranularität">
      <o-select v-model="timeGranularity">
        <option>Täglich</option>
        <option>Monatlich</option>
        <option>Jährlich</option>
      </o-select>
    </o-field>
    <o-field label="Ansicht">
      <o-select v-model="spendingView">
        <option>Absolut</option>
        <option>Kumulativ</option>
      </o-select>
    </o-field>
    <o-field label="Sortieren nach">
      <o-select v-model="topView">
        <option>Menge</option>
        <option>Ausgaben</option>
      </o-select>
    </o-field>
    <o-field label="Anzahl anzeigen">
      <o-slider v-model="topLimit" :min="5" :max="50" :step="5" />
    </o-field>
  </form>
</template>
```

Keep `DashboardPage.vue` responsible for loading/error/empty state and section rendering, but restyle it with Tailwind utilities instead of component-local page CSS. Use `DashboardSection.vue` as the shared section frame with Tailwind surfaces and spacing.

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd web && npm test -- --run src/components/__tests__/DashboardFilterBar.spec.ts src/components/__tests__/DashboardPage.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/components/DashboardPage.vue web/src/components/DashboardFilterBar.vue web/src/components/DashboardSection.vue web/src/App.vue web/src/components/__tests__/DashboardPage.spec.ts web/src/components/__tests__/DashboardFilterBar.spec.ts
git commit -m "feat: restyle dashboard shell and filters"
```

---

### Task 3: Restyle panels and finish verification

**Files:**
- Modify: `web/src/components/KpiRow.vue`
- Modify: `web/src/components/TrendChartPanel.vue`
- Modify: `web/src/components/WeekdayPanel.vue`
- Modify: `web/src/components/TopItemsPanel.vue`
- Modify: `web/src/components/DashboardSkeleton.vue`
- Create: `web/src/components/__tests__/DashboardPanels.spec.ts`

**Interfaces:**
- Consumes: the existing section item arrays from `DashboardPayload.sections[*].items`
- Produces: Tailwind-styled KPI cards, lists, and skeleton state that still render the same payload fields

- [ ] **Step 1: Write the failing test**

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import KpiRow from "../KpiRow.vue";
import TrendChartPanel from "../TrendChartPanel.vue";
import WeekdayPanel from "../WeekdayPanel.vue";
import TopItemsPanel from "../TopItemsPanel.vue";
import DashboardSkeleton from "../DashboardSkeleton.vue";

describe("dashboard panels", () => {
  it("renders the core payload fields", () => {
    expect(
      mount(KpiRow, {
        props: { items: [{ label: "Ausgaben gesamt", value: "€10.00" }] },
      }).text(),
    ).toContain("Ausgaben gesamt");

    expect(
      mount(TrendChartPanel, {
        props: { items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }] },
      }).text(),
    ).toContain("2024-01");

    expect(
      mount(WeekdayPanel, {
        props: { items: [{ weekday_name: "Montag", trip_count: 1, avg_spent: 10, total_spent: 10 }] },
      }).text(),
    ).toContain("Montag");

    expect(
      mount(TopItemsPanel, {
        props: { items: [{ name: "Apfel", total_quantity: 2, total_spent: 4, purchase_count: 1, unit: "pc" }] },
      }).text(),
    ).toContain("Apfel");

    expect(mount(DashboardSkeleton).text()).toBe("");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd web && npm test -- --run src/components/__tests__/DashboardPanels.spec.ts`

Expected: FAIL because the panel components still use the old plain CSS surface styling.

- [ ] **Step 3: Write the minimal implementation**

```vue
<!-- Example pattern for KpiRow.vue -->
<template>
  <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
    <article v-for="item in items" :key="text(item.label)" class="rounded-2xl border border-slate-200 bg-slate-50 p-4 shadow-sm">
      <span class="text-xs font-medium uppercase tracking-wide text-slate-500">{{ text(item.label) }}</span>
      <strong class="mt-1 block text-2xl font-semibold text-slate-900">{{ text(item.value) }}</strong>
    </article>
  </div>
</template>
```

Apply the same Tailwind surface pattern to `TrendChartPanel.vue`, `WeekdayPanel.vue`, `TopItemsPanel.vue`, and `DashboardSkeleton.vue`: keep the same text and fields, but replace handcrafted CSS blocks with Tailwind utility classes and a calmer, more consistent visual hierarchy.

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd web && npm test -- --run src/components/__tests__/DashboardPanels.spec.ts src/components/__tests__/DashboardPage.spec.ts && npm run build`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/components/KpiRow.vue web/src/components/TrendChartPanel.vue web/src/components/WeekdayPanel.vue web/src/components/TopItemsPanel.vue web/src/components/DashboardSkeleton.vue web/src/components/__tests__/DashboardPanels.spec.ts
git commit -m "feat: restyle dashboard panels"
```
