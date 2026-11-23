// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vite-plus/test";

import ImportErrorDetails from "../ImportErrorDetails.vue";

describe("ImportErrorDetails", () => {
  it("shows the debug button and reveals code on demand", async () => {
    const wrapper = mount(ImportErrorDetails, {
      props: {
        errorCode: 4008,
      },
    });

    expect(wrapper.text()).toContain("Fehlercode anzeigen");
    expect(wrapper.text()).not.toContain("Code 4008");

    await wrapper.get("button").trigger("click");

    expect(wrapper.text()).toContain("Fehlercode verbergen");
    expect(wrapper.text()).toContain("Fehlercode 4008");
  });
});
