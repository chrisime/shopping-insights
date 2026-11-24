// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vite-plus/test";
import Oruga from "@oruga-ui/oruga-next";

import DashboardFilterBar from "../DashboardFilterBar.vue";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("DashboardFilterBar", () => {
  it("emits model updates when the user changes search or sort", async () => {
    const wrapper = mount(DashboardFilterBar, {
      props: {
        search: "",
        topView: "Menge",
      },
      global: {
        plugins: [Oruga],
      },
    });

    await wrapper.find("[data-testid=dashboard-search]").setValue("milch");

    expect(wrapper.emitted("update:search")?.at(-1)).toEqual(["milch"]);
    expect(wrapper.find("[data-testid=dashboard-search-field]").exists()).toBe(true);
    expect(wrapper.find("[data-testid=dashboard-filter-form]").classes()).toContain("rounded-2xl");

    await wrapper.find("[data-testid=dashboard-sort]").setValue("Ausgaben");

    expect(wrapper.emitted("update:topView")?.at(-1)).toEqual(["Ausgaben"]);
  });
});
