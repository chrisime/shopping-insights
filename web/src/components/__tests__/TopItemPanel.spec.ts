// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import Oruga, { OSelect } from "@oruga-ui/oruga-next";
import { describe, expect, it } from "vite-plus/test";

import TopItemsPanel from "../TopItemsPanel.vue";

describe("top items panel", () => {
  it("renders the top items table and article values", () => {
    const topItems = mount(TopItemsPanel, {
      props: {
        items: [
          { name: "Apfel", total_quantity: 2.9, total_spent: 4, purchase_count: 1, unit: "pc" },
        ],
        page: 1,
        pageSize: 20,
        totalCount: 1,
        topLimit: 20,
      },
      global: {
        plugins: [Oruga],
      },
    });
    expect(topItems.find("[data-testid=top-items-table]").exists()).toBe(true);
    expect(topItems.text()).toContain("Artikel");
    expect(topItems.text()).toContain("Gesamtmenge");
    expect(topItems.text()).toContain("Ausgaben");
    expect(topItems.text()).toContain("Einkäufe");
    expect(topItems.text()).toContain("Apfel");
    expect(topItems.text()).toContain("2");
    expect(topItems.text()).toContain("2,9 pc");
    expect(topItems.text()).toContain("4,00 €");
    expect(topItems.text()).toContain("1");
    expect(topItems.text()).toContain("pc");
  });

  it("renders fractional quantities for items sold by weight", () => {
    const topItems = mount(TopItemsPanel, {
      props: {
        items: [
          {
            name: "Tomaten",
            total_quantity: 0.696,
            total_spent: 3.99,
            purchase_count: 1,
            unit: "kg",
          },
        ],
        page: 1,
        pageSize: 20,
        totalCount: 1,
        topLimit: 20,
      },
      global: {
        plugins: [Oruga],
      },
    });

    expect(topItems.text()).toContain("Tomaten");
    expect(topItems.text()).toContain("0,696 kg");
    expect(topItems.text()).toContain("3,99 €");
  });

  it("emits numeric page sizes when the top items selection changes", async () => {
    const topItems = mount(TopItemsPanel, {
      props: { items: [], page: 1, pageSize: 20, topLimit: 20, totalCount: 60 },
      global: { plugins: [Oruga] },
    });

    const select = topItems.get("[data-testid=top-items-page-size]");
    await select.setValue("50");
    await select.setValue("10");

    expect(topItems.emitted("update:topLimit")).toEqual([[50], [10]]);
  });

  it("keeps the current top items page size when the selection is undefined", async () => {
    const topItems = mount(TopItemsPanel, {
      props: { items: [], page: 1, pageSize: 20, topLimit: 20, totalCount: 60 },
      global: { plugins: [Oruga] },
    });

    const select = topItems.getComponent(OSelect);
    select.vm.$emit("update:modelValue", undefined);
    await topItems.vm.$nextTick();

    expect(topItems.emitted("update:topLimit")).toBeUndefined();
    expect(topItems.get<HTMLSelectElement>("[data-testid=top-items-page-size]").element.value).toBe(
      "20",
    );
  });

  it("emits the previous and next page from the pagination buttons", async () => {
    const topItems = mount(TopItemsPanel, {
      props: { items: [], page: 2, pageSize: 20, topLimit: 20, totalCount: 45 },
      global: { plugins: [Oruga] },
    });

    const previous = topItems.get<HTMLButtonElement>("[data-testid=top-items-previous]");
    const next = topItems.get<HTMLButtonElement>("[data-testid=top-items-next]");
    expect(previous.element.disabled).toBe(false);
    expect(next.element.disabled).toBe(false);

    await previous.trigger("click");
    await next.trigger("click");

    expect(topItems.emitted("update:page")).toEqual([[1], [3]]);
  });

  it("disables the previous button on the first page and the next button on the last page", async () => {
    const topItems = mount(TopItemsPanel, {
      props: { items: [], page: 1, pageSize: 20, topLimit: 20, totalCount: 45 },
      global: { plugins: [Oruga] },
    });

    const previous = topItems.get<HTMLButtonElement>("[data-testid=top-items-previous]");
    const next = topItems.get<HTMLButtonElement>("[data-testid=top-items-next]");
    expect(previous.element.disabled).toBe(true);
    expect(next.element.disabled).toBe(false);

    await topItems.setProps({ page: 3 });

    expect(previous.element.disabled).toBe(false);
    expect(next.element.disabled).toBe(true);
  });

  it("emits the clicked article's name when its row is selected", async () => {
    const topItems = mount(TopItemsPanel, {
      props: {
        items: [
          { name: "Apfel", total_quantity: 2, total_spent: 4, purchase_count: 1, unit: "pc" },
          { name: "Birne", total_quantity: 3, total_spent: 6, purchase_count: 1, unit: "pc" },
        ],
        page: 1,
        pageSize: 20,
        topLimit: 20,
        totalCount: 2,
      },
      global: { plugins: [Oruga] },
    });

    await topItems.get('[data-testid="top-item-Birne"]').trigger("click");

    expect(topItems.emitted("select-article")).toEqual([["Birne"]]);
  });
});
