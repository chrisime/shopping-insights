// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi, afterEach } from "vitest";

import ReceiptListModal from "../ReceiptListModal.vue";

const TELEPORT_STUB = { template: "<div><slot /></div>" };

function mountModal(props: Record<string, unknown>) {
  return mount(ReceiptListModal, {
    props,
    global: { stubs: { Teleport: TELEPORT_STUB } },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

function stubFetch(data: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => data }),
  );
}

async function settled() {
  await new Promise((resolve) => setTimeout(resolve, 0));
  await new Promise((resolve) => setTimeout(resolve, 0));
}

describe("ReceiptListModal", () => {
  it("renders receipt details from API response", async () => {
    stubFetch([
      {
        id: "r1",
        retailer: "lidl",
        purchase_date: "2024-01-15",
        store: "Lidl München",
        address: { street: "Bahnhofstr.", street_no: "1", zip: "80335", city: "München" },
        total_price: 42.50,
        items: [{ name: "Apfel", quantity: 3, unit: "stk", price: 1.99 }],
        payment_methods: [{ method: "EC-Karte", amount: 42.50 }],
      },
    ]);

    const wrapper = mountModal({ startDate: "2024-01-01", endDate: "2024-01-31", visible: false });
    await wrapper.setProps({ visible: true });
    await settled();

    expect(wrapper.text()).toContain("Januar 2024");
    expect(wrapper.text()).toContain("Lidl München");
    expect(wrapper.text()).toContain("€42.50");
    expect(wrapper.text()).toContain("Apfel");
  });

  it("shows loading state while fetching", async () => {
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));

    const wrapper = mountModal({ startDate: "2024-01-01", endDate: "2024-01-31", visible: false });
    await wrapper.setProps({ visible: true });
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("Lade Kassenzettel");
  });

  it("shows empty state when no receipts found", async () => {
    stubFetch([]);

    const wrapper = mountModal({ startDate: "2024-01-01", endDate: "2024-01-31", visible: false });
    await wrapper.setProps({ visible: true });
    await settled();

    expect(wrapper.text()).toContain("Keine Kassenzettel gefunden");
  });

  it("emits close when background overlay is clicked", async () => {
    stubFetch([]);

    const wrapper = mountModal({ startDate: "2024-01-01", endDate: "2024-01-31", visible: false });
    await wrapper.setProps({ visible: true });
    await settled();

    await wrapper.find(".fixed.inset-0").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
  });

  it("computes monthly label from date range", async () => {
    stubFetch([{
      id: "r1", retailer: "lidl", purchase_date: "2024-01-15",
      total_price: 10.0, items: [], payment_methods: [],
    }]);

    const wrapper = mountModal({ startDate: "2024-01-01", endDate: "2024-01-31", visible: false });
    await wrapper.setProps({ visible: true });
    await settled();

    expect(wrapper.text()).toContain("Januar 2024");
  });

  it("computes daily label from date range", async () => {
    stubFetch([{
      id: "r1", retailer: "lidl", purchase_date: "2024-01-15",
      total_price: 10.0, items: [], payment_methods: [],
    }]);

    const wrapper = mountModal({ startDate: "2024-01-15", endDate: "2024-01-15", visible: false });
    await wrapper.setProps({ visible: true });
    await settled();

    expect(wrapper.text()).toContain("15. Januar 2024");
  });

  it("computes yearly label from date range", async () => {
    stubFetch([{
      id: "r1", retailer: "lidl", purchase_date: "2024-06-15",
      total_price: 10.0, items: [], payment_methods: [],
    }]);

    const wrapper = mountModal({ startDate: "2024-01-01", endDate: "2024-12-31", visible: false });
    await wrapper.setProps({ visible: true });
    await settled();

    expect(wrapper.text()).toContain("2024");
  });
});
