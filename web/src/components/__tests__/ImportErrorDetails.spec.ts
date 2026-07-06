// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ImportErrorDetails from "../ImportErrorDetails.vue";

describe("ImportErrorDetails", () => {
  it("shows the debug button and reveals code on demand", async () => {
    const wrapper = mount(ImportErrorDetails, {
      props: {
        errorCode: 2102,
      },
    });

    expect(wrapper.text()).toContain("Debug-Infos anzeigen");
    expect(wrapper.text()).not.toContain("Code 2102");

    await wrapper.get("button").trigger("click");

    expect(wrapper.text()).toContain("Debug-Infos verbergen");
    expect(wrapper.text()).toContain("Code 2102");
  });
});
