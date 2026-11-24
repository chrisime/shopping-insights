// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vite-plus/test";

import ImportJobControls from "../ImportJobControls.vue";

describe("ImportJobControls", () => {
  it("shows the import selector, button, and progress text", async () => {
    const wrapper = mount(ImportJobControls, {
      props: {
        retailer: "lidl",
        running: false,
        progress: {
          current: 1,
          total: 3,
          added: 1,
          skipped: 0,
          errors: 0,
          items: 4,
          current_receipt: "r1",
        },
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
    expect(wrapper.findAll("[data-testid=import-option]").length).toBeGreaterThanOrEqual(8);
    expect(
      wrapper.findAll<HTMLOptionElement>("[data-testid=import-option]")[0].element.selected,
    ).toBe(true);
    expect(wrapper.find("[data-testid=import-progress-track]").exists()).toBe(true);
  });

  it("defaults lidl and rewe to browser auth", async () => {
    const lidlWrapper = mount(ImportJobControls, {
      props: {
        retailer: "lidl",
        running: false,
        progress: {
          current: 0,
          total: 0,
          added: 0,
          skipped: 0,
          errors: 0,
          items: 0,
          current_receipt: "-",
        },
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
        progress: {
          current: 0,
          total: 0,
          added: 0,
          skipped: 0,
          errors: 0,
          items: 0,
          current_receipt: "-",
        },
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
    await reweWrapper.get("[data-testid=import-customer-id-toggle]").trigger("click");
    expect(reweWrapper.findAll("[data-testid=import-customer-id]").length).toBe(1);
  });

  it("renders technical error details", async () => {
    const wrapper = mount(ImportJobControls, {
      props: {
        retailer: "lidl",
        running: false,
        progress: {
          current: 0,
          total: 0,
          added: 0,
          skipped: 0,
          errors: 1,
          items: 0,
          current_receipt: "-",
        },
        message: "Import fehlgeschlagen",
        error: "Import fehlgeschlagen: Nicht autorisiert (401)",
        technicalError: { error_code: 4008, detail: "Nicht autorisiert (401)" },
      },
      global: {
        stubs: {
          OField: { template: "<div><slot /></div>" },
          OSelect: { template: "<select><slot /></select>" },
        },
      },
    });

    expect(wrapper.text()).toContain("Fehlercode anzeigen");
    expect(wrapper.text()).not.toContain("Code 4008");

    await wrapper.get("[data-testid=import-error-details-toggle]").trigger("click");

    expect(wrapper.text()).toContain("Fehlercode 4008");
  });

  it("emits start-import when the form is submitted", async () => {
    const wrapper = mount(ImportJobControls, {
      props: {
        retailer: "lidl",
        running: false,
        progress: {
          current: 0,
          total: 0,
          added: 0,
          skipped: 0,
          errors: 0,
          items: 0,
          current_receipt: "-",
        },
        message: null,
        error: null,
        technicalError: null,
      },
      global: {
        stubs: {
          OField: { template: "<div><slot /></div>" },
          OSelect: {
            props: ["modelValue"],
            emits: ["update:modelValue"],
            template: `<select :value="modelValue" @change="$emit('update:modelValue', $event.target.value)"><slot /></select>`,
          },
        },
      },
    });

    const browserSelect = wrapper.get('select:has(option[value="firefox"])');
    expect(
      browserSelect.findAll("option").map((option) => [option.element.value, option.text()]),
    ).toEqual([
      ["firefox", "Firefox"],
      ["librewolf", "LibreWolf"],
      ["chrome", "Chrome"],
      ["chromium", "Chromium"],
    ]);

    await browserSelect.setValue("librewolf");
    await wrapper.get("[data-testid=import-form]").trigger("submit");

    expect(wrapper.emitted("start-import")?.[0][0]).toEqual({
      retailer: "lidl",
      browser: "librewolf",
    });
  });

  it("offers dm as an import retailer", async () => {
    const wrapper = mount(ImportJobControls, {
      props: {
        retailer: "dm",
        running: false,
        progress: {
          current: 0,
          total: 0,
          added: 0,
          skipped: 0,
          errors: 0,
          items: 0,
          current_receipt: "-",
        },
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

    const optionValues = wrapper
      .findAll("[data-testid=import-option]")
      .map((o) => o.attributes("value"));
    expect(optionValues).toContain("dm");
  });

  it("emits start-import for dm without customer_id", async () => {
    const wrapper = mount(ImportJobControls, {
      props: {
        retailer: "dm",
        running: false,
        progress: {
          current: 0,
          total: 0,
          added: 0,
          skipped: 0,
          errors: 0,
          items: 0,
          current_receipt: "-",
        },
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

    await wrapper.get("[data-testid=import-form]").trigger("submit");

    expect(wrapper.emitted("start-import")?.[0][0]).toEqual({ retailer: "dm", browser: "firefox" });
  });

  it("starts a Rossmann account import and clears the password", async () => {
    const wrapper = mount(ImportJobControls, {
      props: {
        retailer: "rossmann",
        running: false,
        progress: {
          current: 0,
          total: 0,
          added: 0,
          skipped: 0,
          errors: 0,
          items: 0,
          current_receipt: "-",
        },
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

    const password = wrapper.get<HTMLInputElement>("[data-testid=import-password]");
    expect(wrapper.get("[data-testid=import-submit]").attributes("disabled")).toBeDefined();
    await wrapper.get("[data-testid=import-email]").setValue("person@example.test");
    await password.setValue("test-password");
    await wrapper.get("[data-testid=import-form]").trigger("submit");

    expect(wrapper.emitted("start-import")?.[0][0]).toEqual({
      retailer: "rossmann",
      user_login: { email: "person@example.test", password: "test-password" },
    });
    expect(password.element.value).toBe("");
  });
});
