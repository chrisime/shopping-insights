// @vitest-environment jsdom

import { shallowRef } from "vue";
import { describe, expect, it, vi } from "vite-plus/test";

import { useTimelineScroll } from "../useTimelineScroll";

const setup = (startValue = 0, endValue = 11) => {
  const chart = {
    getOption: vi.fn(() => ({ dataZoom: [{ startValue, endValue }] })),
    getDom: () => document.createElement("div"),
    getWidth: () => 320,
    containPixel: vi.fn(() => true),
    dispatchAction: vi.fn(),
  };
  const { scrollTimeline, resetScroll } = useTimelineScroll(() => 24, shallowRef(chart));

  const wheel = (input: WheelEventInit) => {
    const event = new WheelEvent("wheel", { ...input, cancelable: true });
    scrollTimeline(event);
    return event.defaultPrevented;
  };

  const expectRange = (startValue: number, endValue: number) =>
    expect(chart.dispatchAction).toHaveBeenLastCalledWith({
      type: "dataZoom",
      dataZoomIndex: 0,
      startValue,
      endValue,
    });

  return { chart, wheel, expectRange, resetScroll };
};

describe("useTimelineScroll", () => {
  it("accumulates trackpad movement, carries the remainder and changes direction", () => {
    const { chart, wheel, expectRange } = setup();

    for (let index = 0; index < 3; index++) expect(wheel({ deltaX: 8 })).toBe(true);
    expect(chart.dispatchAction).not.toHaveBeenCalled();
    expect(chart.getOption).toHaveBeenCalledTimes(1);

    wheel({ deltaX: 8 });
    expectRange(1, 12);
    wheel({ deltaX: 40 });
    expectRange(2, 13);
    wheel({ deltaX: 24 });
    expectRange(3, 14);
    wheel({ deltaX: -32 });
    expectRange(2, 13);
  });

  it("normalizes line and page wheel input and leaves wheel events at the edges alone", () => {
    const { chart, wheel, expectRange } = setup();

    expect(wheel({ deltaY: -32 })).toBe(false);
    expect(chart.dispatchAction).not.toHaveBeenCalled();
    wheel({ deltaY: 2, deltaMode: WheelEvent.DOM_DELTA_LINE });
    expectRange(1, 12);
    wheel({ deltaY: 2, deltaMode: WheelEvent.DOM_DELTA_PAGE });
    expectRange(12, 23);
    expect(wheel({ deltaY: 32 })).toBe(false);
    expect(chart.dispatchAction).toHaveBeenCalledTimes(2);
  });

  it("ignores modified wheel input and discards accumulated movement outside the plot", () => {
    const { chart, wheel, expectRange } = setup();

    wheel({ deltaX: 24 });
    expect(wheel({ deltaX: 96, ctrlKey: true })).toBe(false);
    chart.containPixel.mockReturnValueOnce(false);
    expect(wheel({ deltaX: 32 })).toBe(false);

    wheel({ deltaX: 8 });
    expect(chart.dispatchAction).not.toHaveBeenCalled();
    wheel({ deltaX: 24 });
    expectRange(1, 12);
  });

  it("reads the updated slider range and discards the remainder after reset", () => {
    const { chart, wheel, expectRange, resetScroll } = setup();

    wheel({ deltaX: 24 });
    chart.getOption.mockReturnValue({ dataZoom: [{ startValue: 5, endValue: 10 }] });
    resetScroll();

    wheel({ deltaX: 8 });
    expect(chart.dispatchAction).not.toHaveBeenCalled();
    wheel({ deltaX: 24 });
    expectRange(6, 11);
  });

  it("leaves wheel events alone when there is no zoom range", () => {
    const { chart, wheel } = setup();
    chart.getOption.mockReturnValue({ dataZoom: [] });

    expect(wheel({ deltaY: 32 })).toBe(false);
    expect(chart.dispatchAction).not.toHaveBeenCalled();
  });
});
