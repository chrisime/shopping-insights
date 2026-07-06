// @vitest-environment jsdom

import { computed, ref } from "vue";
import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import DashboardPage from "../DashboardPage.vue";
import * as dashboardComposable from "../../composables/useDashboard";
import * as exportApi from "../../api/exports";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("DashboardPage export", () => {
  it("exports the current dashboard filters as json", async () => {
    const state = {
      retailer: ref("lidl"),
      startDate: ref("2024-01-01"),
      endDate: ref("2024-01-31"),
      timeGranularity: ref("Täglich"),
      spendingView: ref("Absolut"),
      topView: ref("Menge"),
      topLimit: ref(20),
      payload: ref({
        title: "Shopping Analyzer Dashboard",
        sections: [{ kind: "metrics", title: "Kennzahlen", items: [] }],
        min_date: "2024-01-01",
        max_date: "2024-01-31",
      }),
      loading: ref(false),
      error: ref(null as string | null),
      filters: computed(() => ({
        retailer: state.retailer.value || undefined,
        start_date: state.startDate.value || undefined,
        end_date: state.endDate.value || undefined,
        time_granularity: state.timeGranularity.value,
        spending_view: state.spendingView.value,
        top_view: state.topView.value,
        top_limit: state.topLimit.value,
      })),
      refresh: vi.fn(),
    };

    vi.spyOn(dashboardComposable, "useDashboard").mockReturnValue(state as never);
    const exportSpy = vi.spyOn(exportApi, "exportReceiptsJson").mockResolvedValue();

    const wrapper = mount(DashboardPage, {
      global: {
        stubs: {
          ImportJobControls: {
            props: ["retailer", "running", "progress", "message", "error", "technicalError"],
            template: "<div />",
          },
            DashboardFilterBar: true,
            DashboardSection: true,
            DashboardSkeleton: true,
            KpiGroupGrid: true,
            TrendChartPanel: true,
            WeekdayPanel: true,
            TopItemsPanel: true,
          },
      },
    });

    await wrapper.get("button").trigger("click");

    expect(exportSpy).toHaveBeenCalledWith({
      retailer: "lidl",
      start_date: "2024-01-01",
      end_date: "2024-01-31",
    });
  });
});
