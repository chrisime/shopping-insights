// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import Oruga from "@oruga-ui/oruga-next";

import DashboardFilterBar from "../DashboardFilterBar.vue";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("DashboardFilterBar", () => {
  it("emits model updates when the user changes a filter", async () => {
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    );

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
      global: {
        plugins: [Oruga],
      },
    });

    await wrapper.find("select").setValue("lidl");

    expect(wrapper.emitted("update:retailer")?.at(-1)).toEqual(["lidl"]);
    expect(wrapper.findComponent({ name: "OField" }).exists()).toBe(true);
    expect(wrapper.find("form").classes()).toContain("rounded-2xl");
  });
});
