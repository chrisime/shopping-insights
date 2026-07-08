// @vitest-environment jsdom

import { ref } from "vue";
import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import DashboardPage from "../DashboardPage.vue";
import * as dashboardComposable from "../../composables/useDashboard";
import * as importComposable from "../../composables/useImportJob";

describe("DashboardPage import", () => {
  it("renders the import control and starts an import when clicked", async () => {
    const startImport = vi.fn().mockResolvedValue(undefined);
    const state = {
      progress: ref({ current: 0, total: 0, added: 0, skipped: 0, errors: 0, items: 0, current_receipt: "-" }),
      loading: ref(false),
      running: ref(false),
      message: ref(null as string | null),
      error: ref(null as string | null),
      technicalError: ref(null as { error_code: number; detail: string } | null),
      startImport,
      closeEventSource: vi.fn(),
    };

    vi.spyOn(dashboardComposable, "useDashboard").mockReturnValue({
      retailer: ref("lidl"),
      startDate: ref(""),
      endDate: ref(""),
      timeGranularity: ref("Täglich"),
      spendingView: ref("Absolut"),
      topView: ref("Menge"),
      topLimit: ref(20),
      search: ref(""),
      page: ref(1),
      payload: ref({ title: "Shopping Analyzer Dashboard", sections: [], min_date: null, max_date: null }),
      loading: ref(false),
      error: ref(null),
      filters: ref({}),
      refresh: vi.fn(),
    } as never);
    vi.spyOn(importComposable, "useImportJob").mockReturnValue(state as never);

    const wrapper = mount(DashboardPage, {
      global: {
        stubs: {
        DashboardFilterBar: true,
        ImportJobControls: {
          template: '<button class="import-control" @click="$emit(\'start-import\', { retailer: \'lidl\', browser: \'firefox\' })">Import</button>',
        },
          DashboardSection: true,
          DashboardSkeleton: true,
          DashboardKpiGrid: true,
          TrendChartPanel: true,
          WeekdayPanel: true,
          TopItemsPanel: true,
        },
      },
    });

    expect(wrapper.text()).toContain("Import");
    await wrapper.find("nav button").trigger("click");
    await wrapper.get(".import-control").trigger("click");

    expect(startImport).toHaveBeenCalledWith({ retailer: "lidl", browser: "firefox" });
  });
});
