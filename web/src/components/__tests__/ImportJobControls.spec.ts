// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import ImportJobControls from "../ImportJobControls.vue";

describe("ImportJobControls", () => {
  it("shows the import selector, button, and progress text", async () => {
    const wrapper = mount(ImportJobControls, {
      props: {
        retailer: "lidl",
        running: false,
        progress: { current: 1, total: 3, added: 1, skipped: 0, errors: 0, items: 4, current_receipt: "r1" },
        message: null,
        error: null,
      },
      global: {
        stubs: {
          OField: { template: "<div><slot /></div>" },
          OSelect: { template: "<select><slot /></select>" },
        },
      },
    });

    expect(wrapper.text()).toContain("Import");
    expect(wrapper.text()).toContain("1/3");
    expect(wrapper.text()).toContain("r1");
  });

  it("emits start-import when the button is clicked", async () => {
    const wrapper = mount(ImportJobControls, {
      props: {
        retailer: "lidl",
        running: false,
        progress: { current: 0, total: 0, added: 0, skipped: 0, errors: 0, items: 0, current_receipt: "-" },
        message: null,
        error: null,
      },
      global: {
        stubs: {
          OField: { template: "<div><slot /></div>" },
          OSelect: { template: "<select><slot /></select>" },
        },
      },
    });

    await wrapper.get("button").trigger("click");

    expect(wrapper.emitted("start-import")).toHaveLength(1);
  });
});
