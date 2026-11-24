// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vite-plus/test";

import ImportJobProgress from "../ImportJobProgress.vue";

describe("ImportJobProgress", () => {
  it("shows progress status independently from import form controls", () => {
    const wrapper = mount(ImportJobProgress, {
      props: {
        progress: {
          current: 2,
          total: 4,
          added: 1,
          skipped: 0,
          errors: 1,
          items: 3,
          current_receipt: "receipt-2",
        },
        message: "Import läuft",
        error: "Ein Beleg ist fehlgeschlagen",
        technicalError: { error_code: 4008, detail: "Unauthorized" },
      },
    });

    expect(wrapper.text()).toContain("2/4");
    expect(wrapper.text()).toContain("receipt-2");
    expect(wrapper.text()).toContain("Import läuft");
    expect(wrapper.text()).toContain("Ein Beleg ist fehlgeschlagen");
    expect(wrapper.find("[data-testid=import-progress-fill]").attributes("style")).toContain(
      "width: 50%",
    );
  });
});
