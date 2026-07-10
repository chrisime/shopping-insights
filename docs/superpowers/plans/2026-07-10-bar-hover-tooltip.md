# Bar Hover + Tooltip Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hover over a D3 trend chart bar → bar darkens + SVG tooltip shows total, receipt count, average per receipt, period, and retailer names.

**Architecture:** Pure CSS bar hover (`.bar:hover { fill: #4f46e5 }`); D3 SVG `<g>` tooltip with fixed 180px width, horizontal separator, pointer-events: none, 200ms hide delay. Backend adds `retailers: list[str]` per trend item via `GROUP_CONCAT(DISTINCT s.retailer_code)` in SQL.

**Tech Stack:** Python 3.11, SQLite, D3.js (v7), Vue 3 + vitest + jsdom, TypeScript

## Global Constraints

- `TimeSeriesRow` dataclass is frozen; new field must be `list[str]` with `field(default_factory=list)`
- SQLite `GROUP_CONCAT` returns `NULL` when no rows → handle in Python as `[]`
- Trend items in frontend add `retailers` field; existing tests must still pass
- Tooltip SVG `<g>` uses `pointer-events: none` to not block click/hover on bars
- Tooltip has a 200ms hide delay on bar `mouseleave` so users can read without hover flicker
- No third-party tooltip libraries; plain D3 + SVG `<text>` elements
- Tooltip bg rect has **fixed 180px width** — avoids `getBBox()` which jsdom does not implement

---

### Task 1: Add `retailers` to `TimeSeriesRow` DTO

**Files:**
- Modify: `shared/kpi_dtos.py:34-39`
- Test: `tests/test_kpi_dtos.py` (create)

**Interfaces:**
- Produces: `TimeSeriesRow(period="2024-01", total_spent=10.0, receipt_count=1, retailers=["lidl"])` — new field `retailers: list[str]` with `field(default_factory=list)`

- [ ] **Step 1: Write the failing test**

Create `tests/test_kpi_dtos.py`:

```python
"""Tests for shared KPI DTOs."""

from shared.kpi_dtos import TimeSeriesRow


def test_time_series_row_retailers_default():
    row = TimeSeriesRow(period="2024-01", total_spent=10.0, receipt_count=1)
    assert row.retailers == []


def test_time_series_row_retailers_set():
    row = TimeSeriesRow(
        period="2024-01", total_spent=10.0, receipt_count=1,
        retailers=["lidl", "rewe"],
    )
    assert row.retailers == ["lidl", "rewe"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_kpi_dtos.py -v`
Expected: FAIL with `TypeError: unexpected keyword argument 'retailers'`

- [ ] **Step 3: Write minimal implementation**

Edit `shared/kpi_dtos.py`:

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TimeSeriesRow:
    period: str
    total_spent: float
    receipt_count: int
    retailers: list[str] = field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_kpi_dtos.py -v`
Expected: PASS (2/2)

- [ ] **Step 5: Commit**

```bash
git add shared/kpi_dtos.py tests/test_kpi_dtos.py
git commit -m "feat: add retailers field to TimeSeriesRow DTO"
```

---

### Task 2: Add `GROUP_CONCAT` to SQL queries in `kpi_store.py`

**Files:**
- Modify: `storage/kpi_store.py:174-196` (day), `221-243` (month), `268-290` (year)

**Interfaces:**
- Consumes: `TimeSeriesRow` with `retailers` field from Task 1
- Produces: `spending_by_day/month/year()` return `list[TimeSeriesRow]` with populated `retailers`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_kpi_store.py`:

```python
def test_spending_retailers_included():
    """Time-series rows should have retailers list from GROUP_CONCAT."""
    from storage.kpi_store import MetricsStore
    store = MetricsStore()
    rows = store.spending_by_day()
    assert len(rows) > 0
    for row in rows:
        assert isinstance(row.retailers, list)
        if row.receipt_count > 0:
            assert len(row.retailers) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_kpi_store.py::test_spending_retailers_included -v`
Expected: FAIL — field exists from Task 1 but always `[]`

- [ ] **Step 3: Update three SQL queries**

Edit `storage/kpi_store.py` — add `GROUP_CONCAT(DISTINCT s.retailer_code) AS retailers` to SELECT of all 3 methods:

**`spending_by_day` (SELECT block ~line 174-184):**
```python
sql = f"""
    SELECT
        DATE(p.purchase_date) AS period,
        SUM(p.total_price) AS total_spent,
        COUNT(p.id) AS receipt_count,
        GROUP_CONCAT(DISTINCT s.retailer_code) AS retailers
    FROM purchase p
    JOIN store s ON s.id = p.store_id
    {where}
    GROUP BY DATE(p.purchase_date)
    ORDER BY period
"""
```

Update return block (~line 189-196):
```python
return [
    TimeSeriesRow(
        period=str(row["period"]),
        total_spent=float(row["total_spent"]),
        receipt_count=int(row["receipt_count"]),
        retailers=row["retailers"].split(",") if row["retailers"] else [],
    )
    for row in rows
]
```

**`spending_by_month` (SELECT block ~line 221-231):**
Same change — add `GROUP_CONCAT(DISTINCT s.retailer_code) AS retailers` to SELECT, same return block.

**`spending_by_year` (SELECT block ~line 268-278):**
Same change — add `GROUP_CONCAT(DISTINCT s.retailer_code) AS retailers` to SELECT, same return block.

- [ ] **Step 4: Run test**

Run: `./.venv/bin/python -m pytest tests/test_kpi_store.py::test_spending_retailers_included -v`
Expected: PASS

- [ ] **Step 5: Run full backend suite to verify no regressions**

Run: `./.venv/bin/python -m pytest -q`
Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add storage/kpi_store.py tests/test_kpi_store.py
git commit -m "feat: add retailer GROUP_CONCAT to time-series SQL queries"
```

---

### Task 3: Serialize `retailers` in dashboard service

**Files:**
- Modify: `api/services/dashboard_service.py:491-494`

**Interfaces:**
- Produces: dashboard payload items now include `"retailers": ["lidl"]`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_dashboard_service.py`:

```python
def test_time_series_items_include_retailers(test_db, dashboard_service):
    payload = dashboard_service.build_dashboard_payload(...)
    time_series = next(s for s in payload.sections if s.kind == "time_series")
    for item in time_series.items:
        assert "retailers" in item
        assert isinstance(item["retailers"], list)
```

(Use the same `test_db` and `dashboard_service` fixture patterns from existing tests in that file.)

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_dashboard_service.py::test_time_series_items_include_retailers -v`
Expected: FAIL

- [ ] **Step 3: Update serialization**

Edit `api/services/dashboard_service.py` line 491-494:

```python
items=[
    {
        "period": row.period,
        "total_spent": row.total_spent,
        "receipt_count": row.receipt_count,
        "retailers": row.retailers,
    }
    for row in state.time_series
],
```

- [ ] **Step 4: Run test**

Run: `./.venv/bin/python -m pytest tests/test_dashboard_service.py::test_time_series_items_include_retailers -v`
Expected: PASS

- [ ] **Step 5: Run full backend suite**

Run: `./.venv/bin/python -m pytest -q`
Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add api/services/dashboard_service.py tests/test_dashboard_service.py
git commit -m "feat: serialize retailers in time-series dashboard items"
```

---

### Task 4: Add hover CSS and D3 SVG tooltip to TrendBarChart.vue

**Files:**
- Modify: `web/src/components/TrendBarChart.vue`

**Interfaces:**
- Consumes: `props.items[].retailers` (string array, optional, accessed as `d.retailers as string[] | undefined`)

- [ ] **Step 1: Add `<style scoped>` rules**

Add at end of existing `<style scoped>`:

```css
.bar {
  cursor: pointer;
  transition: fill 0.15s ease;
}
.bar:hover {
  fill: #4f46e5;
}
```

- [ ] **Step 2: Add module-level hide timer variable**

Right before `function computePeriod(...)` (line 13), add:

```typescript
let tooltipHideTimer: ReturnType<typeof setTimeout> | null = null;
```

- [ ] **Step 3: Add tooltip SVG group creation in `drawChart()`**

After `mainSvg.append("g")` for gridlines (~line 133), add:

```typescript
const tooltipW = 180;
const tooltipLineH = 20;
const tooltipPad = 12;

const tooltipG = mainSvg.append("g")
  .attr("class", "tooltip-group")
  .style("display", "none")
  .style("pointer-events", "none");

tooltipG.append("rect")
  .attr("class", "tooltip-bg")
  .attr("x", -tooltipW / 2)
  .attr("y", 0)
  .attr("width", tooltipW)
  .attr("height", 0)
  .attr("rx", 8)
  .attr("ry", 8)
  .attr("fill", "white")
  .attr("stroke", "#e2e8f0")
  .attr("stroke-width", 1)
  .attr("filter", "drop-shadow(0 2px 4px rgba(0,0,0,0.12))");

// Separator line
tooltipG.append("line")
  .attr("class", "tooltip-sep")
  .attr("x1", -tooltipW / 2 + 8)
  .attr("x2", tooltipW / 2 - 8)
  .attr("y1", 0)
  .attr("y2", 0)
  .attr("stroke", "#e2e8f0")
  .attr("stroke-width", 1);

const textStyle = {
  period: { yOffset: 18, fontSize: "14px", fontWeight: "bold", fill: "#1e293b" },
  total: { yOffset: 44, fontSize: "13px", fontWeight: "normal", fill: "#334155" },
  count: { yOffset: 62, fontSize: "13px", fontWeight: "normal", fill: "#334155" },
  avg: { yOffset: 80, fontSize: "13px", fontWeight: "normal", fill: "#334155" },
  retailers: { yOffset: 100, fontSize: "12px", fontWeight: "normal", fill: "#64748b" },
};

Object.entries(textStyle).forEach(([cls, s]) => {
  tooltipG.append("text")
    .attr("class", `tooltip-${cls}`)
    .attr("text-anchor", "middle")
    .attr("x", 0)
    .attr("y", s.yOffset)
    .attr("font-family", "sans-serif")
    .attr("font-size", s.fontSize)
    .attr("font-weight", s.fontWeight)
    .attr("fill", s.fill);
});

// Height for background rect when retailers present (5 lines) vs absent (4 lines)
//   18 (period) + 26 (gap+sep) + 18 (total) + 18 (count) + 18 (avg) + 18 (retailers) + 6 (bottom pad) = ~104 without retailers, ~122 with
```

- [ ] **Step 4: Add mouseenter handler on bar rects**

Update the bar rect chain — add `.on("mouseenter", ...)` and `.on("mouseleave", ...)` after `.on("click", ...)`.

Replace the existing bar chain (lines 166-181):

```typescript
mainSvg.selectAll("rect.bar")
  .data(items)
  .enter()
  .append("rect")
  .attr("class", "bar")
  .attr("x", (_d: unknown, i: number) => xScale(String(i))!)
  .attr("y", (d: Record<string, unknown>) => yScale(amount(d.total_spent)))
  .attr("width", xScale.bandwidth()!)
  .attr("height", (d: Record<string, unknown>) => yScale(0) - yScale(amount(d.total_spent)))
  .attr("fill", "#6366f1")
  .attr("rx", 4)
  .on("click", (_event: unknown, d: Record<string, unknown>) => {
    emit("select-period", computePeriod(String(d.period ?? ""), props.granularity));
  })
  .on("mouseenter", function (this: SVGRectElement, _event: unknown, d: Record<string, unknown>) {
    if (tooltipHideTimer) clearTimeout(tooltipHideTimer);

    const barX = xScale(String(items.indexOf(d)))!;
    const barTop = yScale(amount(d.total_spent));
    const total = amount(d.total_spent);
    const count = amount(d.receipt_count);
    const avg = count > 0 ? total / count : 0;
    const retailers = (d.retailers as string[] | undefined) ?? [];

    // Position tooltip group centered above the bar
    tooltipG.attr("transform", `translate(${barX + xScale.bandwidth()! / 2}, ${barTop})`);

    // Set text content
    const periodLabel = computePeriod(String(d.period ?? ""), props.granularity).label;
    tooltipG.select(".tooltip-period").text(periodLabel);
    tooltipG.select(".tooltip-total").text(`€${total.toFixed(2)}  Gesamt`);
    tooltipG.select(".tooltip-count").text(`${count} Belege`);
    tooltipG.select(".tooltip-avg").text(`€${avg.toFixed(2)}  Ø/Beleg`);

    const hasRetailers = retailers.length > 0;
    tooltipG.select(".tooltip-retailers").text(hasRetailers ? retailers.join(", ") : "");

    // Tooltip height: 6px bottom pad + header 18 + sep 26 + 3 data lines 54 + optional retailer line
    const bodyH = hasRetailers ? 104 : 84;
    const totalH = bodyH + 6;
    tooltipG.select(".tooltip-bg").attr("height", totalH);

    // Position separator line
    tooltipG.select(".tooltip-sep").attr("y1", 22).attr("y2", 22);

    // Position text relative to tooltipG (y=0 = top of tooltip, below the bar)
    tooltipG.select(".tooltip-period").attr("y", 16);
    tooltipG.select(".tooltip-total").attr("y", 42);
    tooltipG.select(".tooltip-count").attr("y", 60);
    tooltipG.select(".tooltip-avg").attr("y", 78);
    if (hasRetailers) {
      tooltipG.select(".tooltip-retailers").attr("y", 98);
    }

    tooltipG.style("display", "block");
  })
  .on("mouseleave", function () {
    tooltipHideTimer = setTimeout(() => {
      tooltipG.style("display", "none");
    }, 200);
  });
```

- [ ] **Step 5: Update data labels z-index**

Data labels (`text.datalabel`) and euro labels (`text.euroLabel`) are currently drawn after bars. Add a `pointer-events: none` via attribute so hovering works on the bars behind them:

In the datalabel chain (line ~183-201), after `.attr("fill", "white")` add:
```typescript
.attr("pointer-events", "none")
```

In the euroLabel chain (line ~203-215), after `.attr("fill", "#475569")` add:
```typescript
.attr("pointer-events", "none")
```

- [ ] **Step 6: Build**

Run: `corepack pnpm build`
Expected: pass

- [ ] **Step 7: Commit**

```bash
git add web/src/components/TrendBarChart.vue
git commit -m "feat: add bar hover darkening and D3 SVG tooltip"
```

---

### Task 5: Remove native `<title>` tooltip

**Files:**
- Modify: `web/src/components/TrendBarChart.vue`

- [ ] **Step 1: Remove `.append("title")` chain**

Remove these 2 lines from the bar rect chain:
```typescript
.append("title")
.text((d: Record<string, unknown>) => `€${amount(d.total_spent).toFixed(2)}\n${amount(d.receipt_count)} Belege`);
```

- [ ] **Step 2: Build**

Run: `corepack pnpm build`
Expected: pass

- [ ] **Step 3: Commit**

```bash
git add web/src/components/TrendBarChart.vue
git commit -m "refactor: remove native title tooltip (replaced by D3 SVG tooltip)"
```

---

### Task 6: Add tooltip hover tests

**Files:**
- Modify: `web/src/components/__tests__/TrendBarChart.spec.ts`

- [ ] **Step 1: Write the tests**

Add before the closing `});` of the `describe` block:

```typescript
it("shows tooltip on bar mouseenter", () => {
  const wrapper = mount(TrendBarChart, {
    props: {
      granularity: "Monatlich",
      items: [
        {
          period: "2024-01",
          total_spent: 100,
          receipt_count: 5,
          retailers: ["lidl"],
        },
      ],
    },
  });

  const rect = wrapper.find("rect.bar");
  rect.trigger("mouseenter");

  const tooltipGroup = wrapper.find(".tooltip-group");
  expect(tooltipGroup.exists()).toBe(true);
  expect(tooltipGroup.attributes("style")).not.toContain("display: none");
});

it("tooltip contains period, total, count, avg, and retailers", () => {
  const wrapper = mount(TrendBarChart, {
    props: {
      granularity: "Monatlich",
      items: [
        {
          period: "2024-01",
          total_spent: 100,
          receipt_count: 5,
          retailers: ["lidl", "rewe"],
        },
      ],
    },
  });

  const rect = wrapper.find("rect.bar");
  rect.trigger("mouseenter");

  expect(wrapper.text()).toContain("Januar 2024");
  expect(wrapper.text()).toContain("€100.00");
  expect(wrapper.text()).toContain("5 Belege");
  expect(wrapper.text()).toContain("€20.00");
  expect(wrapper.text()).toContain("lidl");
  expect(wrapper.text()).toContain("rewe");
});

it("hides tooltip on bar mouseleave after delay", async () => {
  vi.useFakeTimers();
  const wrapper = mount(TrendBarChart, {
    props: {
      granularity: "Monatlich",
      items: [
        {
          period: "2024-01",
          total_spent: 100,
          receipt_count: 5,
          retailers: ["lidl"],
        },
      ],
    },
  });

  const rect = wrapper.find("rect.bar");
  rect.trigger("mouseenter");
  rect.trigger("mouseleave");

  // Immediately after leave, tooltip should still be visible (200ms delay)
  const tooltipGroup = wrapper.find(".tooltip-group");
  expect(tooltipGroup.attributes("style")).not.toContain("display: none");

  // Advance past the 200ms delay
  vi.advanceTimersByTime(201);
  await wrapper.vm.$nextTick();

  expect(tooltipGroup.attributes("style")).toContain("display: none");
  vi.useRealTimers();
});

it("cancel hide timeout on re-enter", async () => {
  vi.useFakeTimers();
  const wrapper = mount(TrendBarChart, {
    props: {
      granularity: "Monatlich",
      items: [
        {
          period: "2024-01",
          total_spent: 100,
          receipt_count: 5,
          retailers: ["lidl"],
        },
      ],
    },
  });

  const rect = wrapper.find("rect.bar");
  rect.trigger("mouseenter");
  rect.trigger("mouseleave");

  // Re-enter before delay expires
  rect.trigger("mouseenter");
  vi.advanceTimersByTime(201);
  await wrapper.vm.$nextTick();

  const tooltipGroup = wrapper.find(".tooltip-group");
  // Tooltip should still be visible because re-enter cancelled the timer
  expect(tooltipGroup.attributes("style")).not.toContain("display: none");

  // Now leave for real
  rect.trigger("mouseleave");
  vi.advanceTimersByTime(201);
  await wrapper.vm.$nextTick();

  expect(tooltipGroup.attributes("style")).toContain("display: none");
  vi.useRealTimers();
});
```

Need to add the `vi` import at the top (if not already there — check existing imports in the test file). If `vi` isn't imported, add:

```typescript
import { vi } from "vitest";
```

- [ ] **Step 2: Run tests**

Run: `corepack pnpm test -- --run src/components/__tests__/TrendBarChart.spec.ts`
Expected: all tests pass

- [ ] **Step 3: Commit**

```bash
git add web/src/components/__tests__/TrendBarChart.spec.ts
git commit -m "test: add tooltip mouseenter/mouseleave tests"
```

---

### Task 7: Final verification

- [ ] **Step 1: Run full test suite**

```bash
./.venv/bin/python -m pytest -q && corepack pnpm test -- --run && corepack pnpm build
```

Expected: all backend tests pass + all frontend tests pass + build succeeds

- [ ] **Step 2: Commit any final fixes**

```bash
git commit -m "chore: final cleanup after tooltip implementation"
```
