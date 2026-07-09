# Month Header Labels for Daily Chart Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Display month names ("Januar 2024") above the day bars in the daily Chart.js chart, with thin vertical separator lines between months.

**Architecture:** A custom Chart.js plugin (`monthHeaderPlugin`) draws month labels and separators in the `afterDraw` hook using pixel positions from `chart.scales.x`. `TrendChartPanel` computes month boundaries from items and passes them to `TrendBarChart` as a new `monthLabels` prop. X-axis labels become day numbers only when `monthLabels` is present.

**Tech Stack:** Chart.js 4, vue-chartjs 5, TypeScript, Vitest + jsdom

## Global Constraints

- Follow existing code style in `web/src/components/` (Vue 3 `<script setup>`, no comments, etc.)
- Use `web/src/utils/format.ts` for `amount`/`text` helpers
- Use full German month names: "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"

---

### Task 1: Create monthHeaderPlugin

**Files:**
- Create: `web/src/chart-plugins/monthHeaderPlugin.ts`
- Test: `web/src/chart-plugins/__tests__/monthHeaderPlugin.spec.ts`

**Interfaces:**
- Consumes: nothing (standalone)
- Produces: `monthHeaderPlugin: Plugin` (Chart.js plugin object with `id: "monthHeader"` and `afterDraw` hook), `MonthLabel` interface

- [ ] **Step 1: Write the failing test**

Create `web/src/chart-plugins/__tests__/monthHeaderPlugin.spec.ts`:

```typescript
import { describe, expect, it } from "vitest";
import { monthHeaderPlugin } from "../monthHeaderPlugin";

// Minimal verification — actual canvas drawing is not testable in jsdom
describe("monthHeaderPlugin", () => {
  it("exports a Chart.js plugin with id monthHeader", () => {
    expect(monthHeaderPlugin).toBeDefined();
    expect(monthHeaderPlugin.id).toBe("monthHeader");
  });

  it("has an afterDraw function", () => {
    expect(typeof monthHeaderPlugin.afterDraw).toBe("function");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd web && corepack pnpm test -- --run src/chart-plugins/__tests__/monthHeaderPlugin.spec.ts 2>&1 | tail -6
```
Expected: FAIL "Cannot find module"

- [ ] **Step 3: Write minimal implementation**

Create `web/src/chart-plugins/monthHeaderPlugin.ts`:

```typescript
import type { Chart, Plugin } from "chart.js";

export interface MonthLabel {
  label: string;
  start: number;
  end: number;
}

export const monthHeaderPlugin: Plugin = {
  id: "monthHeader",
  afterDraw(chart: Chart) {
    const monthLabels: MonthLabel[] | undefined = (chart.options as Record<string, unknown>).monthLabels as MonthLabel[] | undefined;
    if (!monthLabels || monthLabels.length === 0) return;

    const { ctx } = chart;
    const xScale = chart.scales.x;
    if (!xScale) return;

    const yPos = chart.chartArea.top - 6;
    ctx.save();

    for (let i = 0; i < monthLabels.length; i++) {
      const ml = monthLabels[i];
      const leftPx = xScale.getPixelForValue(ml.start);
      const rightPx = xScale.getPixelForValue(ml.end);
      const midX = (leftPx + rightPx) / 2;

      // Draw separator line between months (skip first month)
      if (i > 0) {
        const prevMl = monthLabels[i - 1];
        const prevLastPx = xScale.getPixelForValue(prevMl.end);
        const currFirstPx = xScale.getPixelForValue(ml.start);
        const sepPx = (prevLastPx + currFirstPx) / 2;
        ctx.beginPath();
        ctx.strokeStyle = "#cbd5e1";
        ctx.lineWidth = 1;
        ctx.moveTo(sepPx, yPos - 4);
        ctx.lineTo(sepPx, chart.chartArea.bottom);
        ctx.stroke();
      }

      // Draw month label
      ctx.font = "bold 13px sans-serif";
      ctx.fillStyle = "#475569";
      ctx.textAlign = "center";
      ctx.fillText(ml.label, midX, yPos);
    }

    ctx.restore();
  },
};
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd web && corepack pnpm test -- --run src/chart-plugins/__tests__/monthHeaderPlugin.spec.ts 2>&1 | tail -6
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/chart-plugins/monthHeaderPlugin.ts web/src/chart-plugins/__tests__/monthHeaderPlugin.spec.ts
git commit -m "feat: add monthHeaderPlugin for daily chart month labels"
```

---

### Task 2: Update TrendChartPanel to compute monthLabels

**Files:**
- Modify: `web/src/components/TrendChartPanel.vue`

**Interfaces:**
- Consumes: `MonthLabel` from `../chart-plugins/monthHeaderPlugin`
- Produces: `monthLabels: MonthLabel[]` computed from `props.items` (passed to TrendBarChart)

- [ ] **Step 1: Add monthLabels computed to TrendChartPanel**

Import the interface and add the computed:

```typescript
import { amount, text, euro } from "../utils/format";
import type { MonthLabel } from "../chart-plugins/monthHeaderPlugin";
```

After the `chartGranularity` computed, add:

```typescript
const fullMonthNames = [
  "Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember",
];

const monthLabels = computed<MonthLabel[]>(() => {
  const granularity = props.timeGranularity;
  if (granularity !== "Täglich") return [];
  const items = props.items;
  if (items.length === 0) return [];
  const result: MonthLabel[] = [];
  let start = 0;
  let currentMonth = String(text(items[0].period)).slice(5, 7);
  for (let i = 1; i <= items.length; i++) {
    const month = i < items.length ? String(text(items[i].period)).slice(5, 7) : null;
    if (month !== currentMonth) {
      const year = String(text(items[i - 1].period)).slice(0, 4);
      const monthIndex = Number(currentMonth) - 1;
      result.push({
        label: `${fullMonthNames[monthIndex]} ${year}`,
        start,
        end: i - 1,
      });
      if (month !== null) {
        start = i;
        currentMonth = month;
      }
    }
  }
  return result;
});
```

Then pass it in the template:

```diff
         <TrendBarChart
           v-if="group.items.length > 0"
           :items="group.items"
           :granularity="chartGranularity"
+          :monthLabels="monthLabels"
         />
```

- [ ] **Step 2: Run existing tests to verify nothing broke**

```bash
cd web && corepack pnpm test -- --run src/chart-plugins/__tests__/monthHeaderPlugin.spec.ts src/components/__tests__/DashboardPanels.spec.ts 2>&1 | tail -10
```
Expected: all pass (tests not yet adjusted for daily labels)

- [ ] **Step 3: Commit**

```bash
git add web/src/components/TrendChartPanel.vue
git commit -m "feat: compute monthLabels in TrendChartPanel for daily granularity"
```

---

### Task 3: Update TrendBarChart to accept monthLabels and show day-only x labels

**Files:**
- Modify: `web/src/components/TrendBarChart.vue`

**Interfaces:**
- Consumes: `monthLabels: MonthLabel[]` prop from TrendChartPanel
- Produces: chart with month headers (visual, not testable via text()), day-number x-axis labels when monthLabels present

- [ ] **Step 1: Update TrendBarChart to accept monthLabels prop and register plugin**

```typescript
import { amount, text } from "../utils/format";
import { monthHeaderPlugin } from "../chart-plugins/monthHeaderPlugin";
import type { MonthLabel } from "../chart-plugins/monthHeaderPlugin";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartDataLabels,
  monthHeaderPlugin,
);

const props = defineProps<{
  items: Array<Record<string, unknown>>;
  granularity: string;
  monthLabels?: MonthLabel[];
}>();
```

Update `chartData` to use day numbers when monthLabels is present:

```typescript
const chartData = computed(() => ({
  labels: props.items.map((item) => {
    const raw = text(item.period);
    return props.monthLabels && props.monthLabels.length > 0 ? raw.slice(8, 10) : raw;
  }),
  datasets: [
    {
      label: "Ausgaben",
      data: props.items.map((item) => amount(item.total_spent)),
      backgroundColor: "#6366f1",
      borderRadius: 4,
    },
  ],
}));
```

Update `chartOptions` to pass `monthLabels` through:

```typescript
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  monthLabels: props.monthLabels,
  plugins: {
    // ... rest unchanged
  },
  scales: {
    // ... rest unchanged
  },
}));
```

- [ ] **Step 2: Run tests to verify nothing broke**

```bash
cd web && corepack pnpm test -- --run src/chart-plugins/__tests__/monthHeaderPlugin.spec.ts src/components/__tests__/DashboardPanels.spec.ts 2>&1 | tail -10
```
Expected: all pass (tests not yet adjusted for daily labels)

- [ ] **Step 3: Commit**

```bash
git add web/src/components/TrendBarChart.vue
git commit -m "feat: register monthHeaderPlugin, show day-only x labels in daily chart"
```

---

### Task 4: Update tests for daily chart with month labels

**Files:**
- Modify: `web/src/components/__tests__/DashboardPanels.spec.ts`

- [ ] **Step 1: Update the daily chart assertions**

The daily chart no longer shows full period strings ("2024-01-01") as x-axis labels — only day numbers ("01"). Month names are drawn by the plugin in canvas (not visible in jsdom mock).

Replace the daily section of the "renders the new vertical bar charts" test:

```typescript
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

// x-axis labels show day numbers when monthLabels are present
const dailyMockLabels = daily.find(".mock-labels");
expect(dailyMockLabels.exists()).toBe(true);
expect(dailyMockLabels.text()).toContain("01");
expect(dailyMockLabels.text()).toContain("02");

// Month labels are rendered by the chart plugin (canvas-only, not visible in mock)
// But the group heading "Tage" is still present
expect(daily.text()).toContain("Tage");
expect(daily.findAll("canvas").length).toBe(1);
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
cd web && corepack pnpm test -- --run 2>&1 | tail -10
```
Expected: 44 passed (43 old + 1 new plugin test)

- [ ] **Step 3: Run full backend tests + build**

```bash
./.venv/bin/python -m pytest -q 2>&1 | tail -2
corepack pnpm build 2>&1 | tail -3
```
Expected: 417 passed + build success

- [ ] **Step 4: Commit**

```bash
git add web/src/components/__tests__/DashboardPanels.spec.ts
git commit -m "test: update daily chart assertions for day-only labels + month header plugin"
```
