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
        technicalError: null,
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
    expect(wrapper.findAll("option").length).toBeGreaterThanOrEqual(8);
    expect(wrapper.findAll("option")[0].element.selected).toBe(true);
    expect(wrapper.find(".h-2").exists()).toBe(true);
  });

  it("defaults lidl and rewe to browser auth", async () => {
    const lidlWrapper = mount(ImportJobControls, {
      props: {
        retailer: "lidl",
        running: false,
        progress: { current: 0, total: 0, added: 0, skipped: 0, errors: 0, items: 0, current_receipt: "-" },
        message: null,
        error: null,
        technicalError: null,
      },
      global: {
        stubs: {
          OField: { template: "<div><slot /></div>" },
          OSelect: { template: "<select><slot /></select>" },
        },
      },
    });

    expect(lidlWrapper.text()).toContain("Browser-Profil");
    expect(lidlWrapper.text()).toContain("Firefox");

    const reweWrapper = mount(ImportJobControls, {
      props: {
        retailer: "rewe",
        running: false,
        progress: { current: 0, total: 0, added: 0, skipped: 0, errors: 0, items: 0, current_receipt: "-" },
        message: null,
        error: null,
        technicalError: null,
      },
      global: {
        stubs: {
          OField: { template: "<div><slot /></div>" },
          OSelect: { template: "<select><slot /></select>" },
        },
      },
    });

    expect(reweWrapper.text()).toContain("Browser-Profil");
    expect(reweWrapper.text()).toContain("Firefox");
    await reweWrapper.get("button").trigger("click");
    expect(reweWrapper.findAll("input[type=\"text\"]").length).toBe(1);
  });

  it("renders technical error details", async () => {
    const wrapper = mount(ImportJobControls, {
      props: {
        retailer: "lidl",
        running: false,
        progress: { current: 0, total: 0, added: 0, skipped: 0, errors: 1, items: 0, current_receipt: "-" },
        message: "Import fehlgeschlagen",
        error: "Import fehlgeschlagen: Nicht autorisiert (401)",
        technicalError: { error_code: 2102, detail: "Nicht autorisiert (401)" },
      },
      global: {
        stubs: {
          OField: { template: "<div><slot /></div>" },
          OSelect: { template: "<select><slot /></select>" },
        },
      },
    });

    expect(wrapper.text()).toContain("Debug-Infos anzeigen");
    expect(wrapper.text()).not.toContain("Code 2102");

    await wrapper.findAll("button")[1].trigger("click");

    expect(wrapper.text()).toContain("Code 2102");
  });

  it("emits start-import when the button is clicked", async () => {
    const wrapper = mount(ImportJobControls, {
      props: {
        retailer: "lidl",
        running: false,
        progress: { current: 0, total: 0, added: 0, skipped: 0, errors: 0, items: 0, current_receipt: "-" },
        message: null,
        error: null,
        technicalError: null,
      },
      global: {
        stubs: {
          OField: { template: "<div><slot /></div>" },
          OSelect: { template: "<select><slot /></select>" },
        },
      },
    });

    await wrapper.get("button").trigger("click");

    expect(wrapper.emitted("start-import")?.[0][0]).toEqual({ retailer: "lidl", browser: "firefox" });
  });
});
