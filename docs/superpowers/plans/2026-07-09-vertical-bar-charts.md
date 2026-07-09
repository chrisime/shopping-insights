# Vertical Bar Charts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the horizontal-bar / collapsible-tree spending chart with vertical bar charts rendered by Chart.js, showing receipt-count labels on each bar in a coordinate-system layout.

**Architecture:** A new `TrendBarChart.vue` wraps `vue-chartjs` `<Bar>` component. `TrendChartPanel.vue` is rewritten to group data by year/month and render one `TrendBarChart` per group. No backend changes.

**Tech Stack:** chart.js v4, vue-chartjs, chartjs-plugin-datalabels, Vue 3, TypeScript, Vitest

## Global Constraints

- chart.js v4 (not v3) — use `chart.js` npm package
- `vue-chartjs` must be compatible with Vue 3
- `chartjs-plugin-datalabels` v2 for chart.js v4
- Bar color: indigo-500 (`#6366f1`)
- Receipt-count labels: white text centered inside bar
- Y-axis: spending in EUR, `beginAtZero`
- Monthly/daily charts wrapped in horizontal scroll container (`overflow-x: auto`)
- No backend changes — `time_series` section already provides `{period, total_spent, receipt_count}`

---

### Task 1: Add Chart.js dependencies

**Files:**
- Modify: `web/package.json`
- Run: `pnpm install`

- [ ] **Step 1: Update package.json**

Insert after the existing `dependencies` block:

```json
"chart.js": "^4.4.8",
"chartjs-plugin-datalabels": "^2.2.0",
"vue-chartjs": "^5.3.2",
```

The full `dependencies` section becomes:

```json
  "dependencies": {
    "@oruga-ui/oruga-next": "^0.13.6",
    "@oruga-ui/theme-oruga": "^0.9.1",
    "chart.js": "^4.4.8",
    "chartjs-plugin-datalabels": "^2.2.0",
    "vue": "^3.5.13",
    "vue-chartjs": "^5.3.2"
  },
```

- [ ] **Step 2: Install**

Run: `cd web && corepack pnpm install`

Verify with: `node -e "require('chart.js'); require('vue-chartjs'); console.log('ok')"`

- [ ] **Step 3: Commit**

```bash
git add web/package.json web/pnpm-lock.yaml
git commit -m "deps: add chart.js, vue-chartjs, chartjs-plugin-datalabels"
```

---

### Task 2: Create TrendBarChart.vue

**Files:**
- Create: `web/src/components/TrendBarChart.vue`

**Interfaces:**
- Consumes: items array with `{period, total_spent, receipt_count}` shape
- Produces: `<Bar>` chart component with datalabels plugin

- [ ] **Step 1: Write the test file**

Create `web/src/components/__tests__/TrendBarChart.spec.ts`:

```typescript
// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import TrendBarChart from "../TrendBarChart.vue";

// Mock vue-chartjs Bar component since canvas rendering isn't available in jsdom
vi.mock("vue-chartjs", () => ({
  Bar: { template: "<canvas data-testid='mock-bar-chart' />" },
}));

describe("TrendBarChart", () => {
  it("renders a canvas element", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }],
        granularity: "Monatlich",
      },
    });
    expect(wrapper.find("canvas").exists()).toBe(true);
  });

  it("renders monthly labels", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [
          { period: "2024-01", total_spent: 10, receipt_count: 1 },
          { period: "2024-02", total_spent: 20, receipt_count: 2 },
        ],
        granularity: "Monatlich",
      },
    });
    // Period labels should be rendered as text somewhere
    expect(wrapper.text()).toContain("2024-01");
    expect(wrapper.text()).toContain("2024-02");
  });

  it("wraps chart in scrollable container for monthly granularity", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }],
        granularity: "Monatlich",
      },
    });
    expect(wrapper.find(".overflow-x-auto").exists()).toBe(true);
  });

  it("renders yearly labels", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [
          { period: "2024", total_spent: 100, receipt_count: 12 },
          { period: "2025", total_spent: 200, receipt_count: 24 },
        ],
        granularity: "Jährlich",
      },
    });
    expect(wrapper.text()).toContain("2024");
    expect(wrapper.text()).toContain("2025");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && corepack pnpm test -- --run src/components/__tests__/TrendBarChart.spec.ts`

Expected: FAIL — "Failed to resolve component: Bar" or "Module not found"

- [ ] **Step 3: Write the TrendBarChart component**

Create `web/src/components/TrendBarChart.vue`:

```vue
<script setup lang="ts">
import { computed } from "vue";
import { Bar } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import ChartDataLabels from "chartjs-plugin-datalabels";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartDataLabels,
);

const props = defineProps<{
  items: Array<Record<string, unknown>>;
  granularity: string;
}>();

function amount(value: unknown): number {
  return typeof value === "number" ? value : Number(value ?? 0);
}

function text(value: unknown): string {
  return value == null ? "-" : String(value);
}

const chartData = computed(() => ({
  labels: props.items.map((item) => text(item.period)),
  datasets: [
    {
      label: "Ausgaben",
      data: props.items.map((item) => amount(item.total_spent)),
      backgroundColor: "#6366f1",
      borderRadius: 4,
    },
  ],
}));

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    datalabels: {
      color: "#fff",
      anchor: "center" as const,
      align: "center" as const,
      font: { weight: "bold" as const, size: 12 },
      formatter: (_value: number, ctx: { dataIndex: number }) => {
        const receiptCount = amount(props.items[ctx.dataIndex]?.receipt_count);
        return receiptCount > 0 ? String(receiptCount) : "";
      },
    },
    tooltip: {
      callbacks: {
        label: (ctx: { parsed: { y: number }; dataIndex: number }) => {
          const receiptCount = amount(props.items[ctx.dataIndex]?.receipt_count);
          return [`€${ctx.parsed.y.toFixed(2)}`, `${receiptCount} Belege`];
        },
      },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { maxRotation: 45 },
    },
    y: {
      beginAtZero: true,
      grid: { color: "#e2e8f0" },
      ticks: {
        callback: (value: number) => `€${value.toFixed(0)}`,
      },
    },
  },
}));

const isScrollable = computed(() => props.granularity !== "Jährlich");
</script>

<template>
  <div v-if="isScrollable" class="overflow-x-auto">
    <div class="h-64" :style="{ minWidth: `${items.length * 48}px` }">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </div>
  <div v-else class="h-64">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && corepack pnpm test -- --run src/components/__tests__/TrendBarChart.spec.ts`

Expected: PASS (tests adjust for jsdom limitations — the canvas mock and text checks should work)

- [ ] **Step 5: Commit**

```bash
git add web/src/components/TrendBarChart.vue web/src/components/__tests__/TrendBarChart.spec.ts
git commit -m "feat: add TrendBarChart vertical bar chart component"
```

---

### Task 3: Rewrite TrendChartPanel.vue

**Files:**
- Modify: `web/src/components/TrendChartPanel.vue` (complete rewrite)

**Interfaces:**
- Consumes: `TrendBarChart` component, `items` array, `spendingView`, `timeGranularity` props
- Produces: Summary cards + grouped vertical bar charts

- [ ] **Step 1: Write the TrendBarChart items grouping logic first (no-chart version)**

At this point we still have the mock, so the test can verify grouping without chart rendering.

- [ ] **Step 2: Write tests for the rewritten TrendChartPanel**

Update `web/src/components/__tests__/DashboardPanels.spec.ts`:

Replace the `TrendChartPanel`-related tests (lines 13–61) with:

```typescript
  it("renders the new vertical bar charts", () => {
    const monthly = mount(TrendChartPanel, {
      props: {
        timeGranularity: "Monatlich",
        items: [
          { period: "2023-01", total_spent: 10, receipt_count: 1 },
          { period: "2023-02", total_spent: 20, receipt_count: 2 },
          { period: "2024-01", total_spent: 30, receipt_count: 3 },
        ],
      },
    });

    expect(monthly.text()).toContain("2023");
    expect(monthly.text()).toContain("2023-01");
    expect(monthly.text()).toContain("€10.00");
    expect(monthly.findAll("canvas").length).toBeGreaterThanOrEqual(1);

    const daily = mount(TrendChartPanel, {
      props: {
        timeGranularity: "Täglich",
        items: [
          { period: "2024-01-01", total_spent: 10, receipt_count: 1 },
          { period: "2024-01-02", total_spent: 20, receipt_count: 2 },
          { period: "2024-02-01", total_spent: 30, receipt_count: 3 },
        ],
      },
    });

    expect(daily.text()).toContain("2024");
    expect(daily.text()).toContain("Jan");
    expect(daily.text()).toContain("Feb");
    expect(daily.text()).toContain("01");
    expect(daily.findAll("canvas").length).toBeGreaterThanOrEqual(2);

    const trend = mount(TrendChartPanel, {
      props: { items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }, { period: "2024-02", total_spent: 5, receipt_count: 2 }] },
    });
    expect(trend.text()).toContain("2024-01");
    expect(trend.text()).toContain("€10.00");
    expect(trend.findAll("canvas").length).toBeGreaterThanOrEqual(1);
  });
```

Remove the old assertions:
- `monthly.findAll(".bg-indigo-500")` — Chart.js bars are on canvas, not DOM
- `monthly.findAll("details")` — daily no longer uses collapsible tree
- `monthly.findAll("svg")` — no more chevron SVGs
- `.attributes("style")` — no more inline bar widths

The `zeroTrend` test (line 58) can also be removed since bar widths are now handled by Chart.js internally.

- [ ] **Step 3: Run test to verify it fails**

Run: `cd web && corepack pnpm test -- --run src/components/__tests__/DashboardPanels.spec.ts`

Expected: FAIL — old TrendChartPanel still returns old markup

- [ ] **Step 4: Rewrite TrendChartPanel.vue**

Replace the entire content of `web/src/components/TrendChartPanel.vue`:

```vue
<script setup lang="ts">
import { computed } from "vue";
import TrendBarChart from "./TrendBarChart.vue";

const props = defineProps<{
  items: Array<Record<string, unknown>>;
  spendingView?: string;
  timeGranularity?: string;
}>();

function amount(value: unknown): number {
  return typeof value === "number" ? value : Number(value ?? 0);
}

function text(value: unknown): string {
  return value == null ? "-" : String(value);
}

function monthName(value: string): string {
  const names = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"];
  const index = Number(value) - 1;
  return names[index] ?? value;
}
const summary = computed(() => {
  if (props.spendingView !== "Absolut" || props.items.length === 0) {
    return null;
  }
  const values = props.items.map((item) => amount(item.total_spent));
  const total = values.reduce((sum, value) => sum + value, 0);
  return {
    average: total / values.length,
    maximum: Math.max(...values),
    minimum: Math.min(...values),
  };
});

type GroupNode = {
  label: string;
  key: string;
  items: Array<Record<string, unknown>>;
};

function buildYearGroups(granularity: string): GroupNode[] {
  const map = new Map<string, GroupNode>();
  for (const item of props.items) {
    const period = text(item.period);
    const year = period.slice(0, 4);
    if (!map.has(year)) {
      map.set(year, { label: year, key: year, items: [] });
    }
    map.get(year)!.items.push(item);
  }
  return [...map.values()];
}

function buildMonthGroups(): GroupNode[] {
  const map = new Map<string, GroupNode>();
  for (const item of props.items) {
    const period = text(item.period);
    const year = period.slice(0, 4);
    const month = period.slice(5, 7);
    const yearKey = year;
    if (!map.has(yearKey)) {
      map.set(yearKey, { label: year, key: yearKey, items: [] });
    }
    const node = map.get(yearKey)!;
    const label = `${monthName(month)} ${year}`;
    node.items.push({ ...item, period: label });
  }
  return [...map.values()];
}

function buildDayGroups(): GroupNode[] {
  const yearMap = new Map<string, { label: string; key: string; monthNodes: Map<string, GroupNode> }>();
  for (const item of props.items) {
    const period = text(item.period);
    const year = period.slice(0, 4);
    const month = period.slice(5, 7);
    const day = period.slice(8, 10);
    if (!yearMap.has(year)) {
      yearMap.set(year, { label: year, key: year, monthNodes: new Map() });
    }
    const yearEntry = yearMap.get(year)!;
    const monthKey = `${year}-${month}`;
    if (!yearEntry.monthNodes.has(monthKey)) {
      const label = `${monthName(month)} ${year}`;
      yearEntry.monthNodes.set(monthKey, { label, key: monthKey, items: [] });
    }
    yearEntry.monthNodes.get(monthKey)!.items.push({ ...item, period: day });
  }
  const result: GroupNode[] = [];
  for (const yearEntry of yearMap.values()) {
    result.push({ label: yearEntry.label, key: yearEntry.key, items: [] });
    for (const monthNode of yearEntry.monthNodes.values()) {
      result.push(monthNode);
    }
  }
  return result;
}

const groups = computed(() => {
  const granularity = props.timeGranularity || "Monatlich";
  if (granularity === "Monatlich") {
    return buildMonthGroups();
  }
  if (granularity === "Täglich") {
    return buildDayGroups();
  }
  return buildYearGroups(granularity);
});

const chartGranularity = computed(() => props.timeGranularity || "Monatlich");
</script>

<template>
  <div class="grid gap-4">
    <div v-if="summary" class="grid gap-3 sm:grid-cols-3">
      <article class="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 shadow-sm">
        <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Ø Ausgaben pro Zeitraum</p>
        <strong class="mt-1 block text-xl font-semibold text-slate-900">{{ euro(summary.average) }}</strong>
      </article>
      <article class="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 shadow-sm">
        <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Maximum</p>
        <strong class="mt-1 block text-xl font-semibold text-slate-900">{{ euro(summary.maximum) }}</strong>
      </article>
      <article class="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 shadow-sm">
        <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Minimum</p>
        <strong class="mt-1 block text-xl font-semibold text-slate-900">{{ euro(summary.minimum) }}</strong>
      </article>
    </div>

    <div class="grid gap-6">
      <div v-for="group in groups" :key="group.key" class="grid gap-2">
        <h3 v-if="group.items.length > 0" class="text-sm font-semibold text-slate-800">{{ group.label }}</h3>
        <TrendBarChart
          v-if="group.items.length > 0"
          :items="group.items"
          :granularity="chartGranularity"
        />
      </div>
    </div>
  </div>
</template>
```

Add the `euro` function — append it after the `amount` function:

```typescript
function euro(value: unknown): string {
  const numeric = amount(value);
  return Number.isFinite(numeric) ? `€${numeric.toFixed(2)}` : "-";
}
```

- [ ] **Step 5: Run all frontend tests**

Run: `cd web && corepack pnpm test -- --run`

Expected: All tests pass (DashboardPanels, TrendBarChart spec, ImportJobControls, etc.)

Fix any failing assertions — the old `.bg-indigo-500` and `style` assertions should have been removed.

- [ ] **Step 6: Commit**

```bash
git add web/src/components/TrendChartPanel.vue web/src/components/__tests__/DashboardPanels.spec.ts
git commit -m "feat: rewrite TrendChartPanel with vertical Chart.js bars"
```

---

### Task 4: Build verification

**Files:**
- Run build to confirm no type errors

- [ ] **Step 1: Run pnpm build**

Run: `cd web && corepack pnpm build`

Expected: Build succeeds with no errors

- [ ] **Step 2: Run all tests one final time**

Run: `cd web && corepack pnpm test -- --run`

Expected: All 38+ tests pass (including the new TrendBarChart spec)

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: update AGENTS.md and verify build"
```
