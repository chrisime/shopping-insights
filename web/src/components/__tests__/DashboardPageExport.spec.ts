// @vitest-environment jsdom

import { ref } from "vue";
import { mount } from "@vue/test-utils";
import Oruga from "@oruga-ui/oruga-next";
import { afterEach, describe, expect, it, vi } from "vite-plus/test";

import { stubDialog } from "../../test/stubDialog";
import DashboardPage from "../DashboardPage.vue";
import * as dashboardComposable from "../../composables/useDashboard";
import * as exportApi from "../../api/exports";

afterEach(() => {
  vi.restoreAllMocks();
});

stubDialog();

describe("DashboardPage export", () => {
  it("exports the current dashboard filters as json", async () => {
    const retailer = ref("lidl");
    const startDate = ref("2024-01-01");
    const endDate = ref("2024-01-31");
    const timeGranularity = ref("daily");
    const topView = ref("Menge");
    const topLimit = ref(20);
    const search = ref("");
    const page = ref(1);
    const payload = ref({
      title: "Shopping Analyzer Dashboard",
      sections: [{ kind: "metrics", title: "Kennzahlen", items: [] }],
      min_date: "2024-01-01",
      max_date: "2024-01-31",
    });
    const loading = ref(false);
    const error = ref(null as string | null);

    const state = {
      retailer,
      startDate,
      endDate,
      timeGranularity,
      topView,
      topLimit,
      search,
      page,
      payload,
      loading,
      error,
      refresh: vi.fn(),
    };

    vi.spyOn(dashboardComposable, "useDashboard").mockReturnValue(state as never);
    const exportSpy = vi.spyOn(exportApi, "exportReceiptsJson").mockResolvedValue();

    const wrapper = mount(DashboardPage, {
      global: {
        plugins: [Oruga],
        stubs: {
          ImportJobControls: {
            props: ["retailer", "running", "progress", "message", "error", "technicalError"],
            template: "<div />",
          },
          DashboardFilterBar: true,
          DashboardSection: true,
          DashboardSkeleton: true,
          DashboardKpiGrid: true,
          TrendChartPanel: true,
          WeekdayPanel: true,
          TopItemsPanel: true,
        },
      },
    });

    await wrapper.find("[data-testid=dashboard-export]").trigger("click");

    expect(exportSpy).toHaveBeenCalledWith({
      retailer: "lidl",
      start_date: "2024-01-01",
      end_date: "2024-01-31",
    });
  });
});
