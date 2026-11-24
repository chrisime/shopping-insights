// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi, afterEach } from "vite-plus/test";

import { stubDialog } from "../../test/stubDialog";
import ReceiptListModal from "../ReceiptListModal.vue";

type ModalProps = {
  startDate: string;
  endDate: string;
  visible: boolean;
  retailer?: string;
};

const mountModal = (props: ModalProps) =>
  mount(ReceiptListModal, {
    props,
  });

afterEach(() => {
  vi.unstubAllGlobals();
});

const stubFetch = (data: unknown) => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => data }));
};

const settled = async () => {
  await new Promise((resolve) => setTimeout(resolve, 0));
  await new Promise((resolve) => setTimeout(resolve, 0));
};

stubDialog();

describe("ReceiptListModal", () => {
  it("shows the oldest receipt first when the API returns receipts in date order", async () => {
    stubFetch([
      {
        id: "r1",
        retailer: "lidl",
        purchase_date: "2024-01-15",
        store: "Lidl München",
        address: { street: "Bahnhofstr.", street_no: "1", zip: "80335", city: "München" },
        total_price: 42.5,
        items: [{ name: "Apfel", quantity: 3, unit: "stk", price: 1.99 }],
        payment_methods: [{ method: "EC-Karte", amount: 42.5 }],
      },
      {
        id: "r2",
        retailer: "lidl",
        purchase_date: "2024-01-24",
        store: "Lidl Augsburg",
        total_price: 10,
        items: [],
        payment_methods: [],
      },
    ]);

    const wrapper = mountModal({ startDate: "2024-01-01", endDate: "2024-01-31", visible: false });
    await wrapper.setProps({ visible: true });
    await settled();

    expect(wrapper.text()).toContain("Januar 2024");
    expect(wrapper.text()).toContain("Lidl München");
    expect(wrapper.text()).toContain("42,50 €");
    expect(wrapper.text()).toContain("Apfel");

    await wrapper.get("[data-testid=receipt-next]").trigger("click");
    expect(wrapper.text()).toContain("Lidl Augsburg");
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
    expect(wrapper.text()).not.toContain("Kassenzettel konnten nicht geladen werden");
  });

  it("shows an error state when receipt loading fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500 }));

    const wrapper = mountModal({ startDate: "2024-01-01", endDate: "2024-01-31", visible: false });
    await wrapper.setProps({ visible: true });
    await settled();

    expect(wrapper.text()).toContain("Die Anfrage ist fehlgeschlagen.");
    expect(wrapper.text()).not.toContain("Keine Kassenzettel gefunden");
  });

  it("emits close when background overlay is clicked", async () => {
    stubFetch([]);

    const wrapper = mountModal({ startDate: "2024-01-01", endDate: "2024-01-31", visible: false });
    await wrapper.setProps({ visible: true });
    await settled();

    await wrapper.find("[data-testid=receipt-overlay]").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
  });

  it("computes monthly label from date range", async () => {
    stubFetch([
      {
        id: "r1",
        retailer: "lidl",
        purchase_date: "2024-01-15",
        total_price: 10.0,
        items: [],
        payment_methods: [],
      },
    ]);

    const wrapper = mountModal({ startDate: "2024-01-01", endDate: "2024-01-31", visible: false });
    await wrapper.setProps({ visible: true });
    await settled();

    expect(wrapper.text()).toContain("Januar 2024");
  });

  it("computes daily label from date range", async () => {
    stubFetch([
      {
        id: "r1",
        retailer: "lidl",
        purchase_date: "2024-01-15",
        total_price: 10.0,
        items: [],
        payment_methods: [],
      },
    ]);

    const wrapper = mountModal({ startDate: "2024-01-15", endDate: "2024-01-15", visible: false });
    await wrapper.setProps({ visible: true });
    await settled();

    expect(wrapper.text()).toContain("15. Januar 2024");
  });

  it("computes yearly label from date range", async () => {
    stubFetch([
      {
        id: "r1",
        retailer: "lidl",
        purchase_date: "2024-06-15",
        total_price: 10.0,
        items: [],
        payment_methods: [],
      },
    ]);

    const wrapper = mountModal({ startDate: "2024-01-01", endDate: "2024-12-31", visible: false });
    await wrapper.setProps({ visible: true });
    await settled();

    expect(wrapper.text()).toContain("2024");
  });
});
