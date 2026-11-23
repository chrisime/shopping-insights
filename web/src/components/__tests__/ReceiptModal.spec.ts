// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vite-plus/test";

import ReceiptModal from "../ReceiptModal.vue";

const TELEPORT_STUB = { template: "<div><slot /></div>" };

function receipt(id: string, matched: boolean) {
  return {
    id,
    retailer: "lidl",
    purchase_date: "2024-01-15",
    store: "Lidl München",
    total_price: 42.5,
    items: [{ name: "Apfel", quantity: 3, unit: "stk", price: 1.99, matched }],
  };
}

function mountModal() {
  return mount(ReceiptModal, {
    props: { articleName: "Apfel", visible: false },
    global: { stubs: { Teleport: TELEPORT_STUB } },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ReceiptModal", () => {
  it("shows the article and retailer in the title and highlights matched items", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => [receipt("r1", true)] }),
    );

    const wrapper = mountModal();
    await wrapper.setProps({ visible: true });
    await new Promise((resolve) => setTimeout(resolve, 0));
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(wrapper.text()).toContain("Apfel — Lidl Kassenzettel");
    expect(wrapper.text()).toContain("Lidl München");
    expect(wrapper.text()).toContain("€42.50");
    expect(wrapper.find(".bg-amber-50").exists()).toBe(true);
  });

  it("does not highlight items without a match", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => [receipt("r1", false)] }),
    );

    const wrapper = mountModal();
    await wrapper.setProps({ visible: true });
    await new Promise((resolve) => setTimeout(resolve, 0));
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(wrapper.find(".bg-amber-50").exists()).toBe(false);
  });

  it("pages through multiple receipts", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [receipt("r1", true), receipt("r2", false)],
      }),
    );

    const wrapper = mountModal();
    await wrapper.setProps({ visible: true });
    await new Promise((resolve) => setTimeout(resolve, 0));
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(wrapper.text()).toContain("1 von 2");
    const next = wrapper.findAll("button").find((button) => button.text() === "Weiter");
    expect(next).toBeDefined();
    await next?.trigger("click");
    expect(wrapper.text()).toContain("2 von 2");
    expect(wrapper.find(".bg-amber-50").exists()).toBe(false);
  });

  it("emits close when the overlay is clicked", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => [] }));

    const wrapper = mountModal();
    await wrapper.setProps({ visible: true });
    await new Promise((resolve) => setTimeout(resolve, 0));

    await wrapper.find(".fixed.inset-0").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
  });
});
