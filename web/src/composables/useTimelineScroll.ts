import type { ECharts } from "echarts/core";
import { useTemplateRef, type Ref } from "vue";

type ScrollChart = Pick<
  ECharts,
  "getOption" | "getDom" | "getWidth" | "containPixel" | "dispatchAction"
>;
type ScrollRange = { startValue: number; endValue: number };

const SCROLL_PIXELS_PER_BAR = 32;
const WHEEL_LINE_HEIGHT = 16;

const wheelDeltaInPixels = (event: WheelEvent, chart: ScrollChart): number => {
  const { deltaX, deltaY, deltaMode } = event;
  const delta = Math.abs(deltaX) > Math.abs(deltaY) ? deltaX : deltaY;
  if (!delta) return 0;
  if (deltaMode === WheelEvent.DOM_DELTA_LINE) return delta * WHEEL_LINE_HEIGHT;
  if (deltaMode === WheelEvent.DOM_DELTA_PAGE) return delta * chart.getWidth();
  return delta;
};

export const useTimelineScroll = (
  itemCount: () => number,
  chartRef: Readonly<Ref<ScrollChart | null>> = useTemplateRef<ScrollChart>("chart"),
) => {
  let pendingScrollPixels = 0;
  let scrollRange: ScrollRange | undefined;

  const resetScroll = () => {
    scrollRange = undefined;
    pendingScrollPixels = 0;
  };

  const scrollTimeline = (event: WheelEvent) => {
    const chart = chartRef.value;
    if (!chart || event.ctrlKey) return;

    const visible = (scrollRange ??= (
      chart.getOption()?.dataZoom as ScrollRange[] | undefined
    )?.[0]);
    if (!visible) return;

    const bounds = chart.getDom().getBoundingClientRect();
    if (
      !chart.containPixel({ gridIndex: 0 }, [
        event.clientX - bounds.left,
        event.clientY - bounds.top,
      ])
    ) {
      pendingScrollPixels = 0;
      return;
    }

    const delta = wheelDeltaInPixels(event, chart);
    const { startValue, endValue } = visible;
    const lastIndex = itemCount() - 1;

    if (!delta || (delta < 0 ? startValue === 0 : endValue === lastIndex)) {
      pendingScrollPixels = 0;
      return;
    }

    event.preventDefault();

    pendingScrollPixels += delta;
    const steps = Math.trunc(pendingScrollPixels / SCROLL_PIXELS_PER_BAR);
    if (!steps) return;

    const shift = Math.max(-startValue, Math.min(steps, lastIndex - endValue));
    const remainingPixels =
      shift === steps ? pendingScrollPixels - steps * SCROLL_PIXELS_PER_BAR : 0;

    const nextRange = { startValue: startValue + shift, endValue: endValue + shift };
    // A synchronous datazoom event can reset state, so save the range and remainder here.
    chart.dispatchAction({ type: "dataZoom", dataZoomIndex: 0, ...nextRange });

    scrollRange = nextRange;
    pendingScrollPixels = remainingPixels;
  };

  return { scrollTimeline, resetScroll };
};
