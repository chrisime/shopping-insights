import type { Chart, Plugin } from "chart.js";

export interface MonthLabel {
  label: string;
  start: number;
  end: number;
}

export const monthHeaderPlugin: Plugin = {
  id: "monthHeader",
  afterDraw(chart: Chart) {
    const monthLabels: MonthLabel[] | undefined = (chart.options as Record<string, unknown>).monthLabels as MonthLabel[] | undefined;
    if (!monthLabels || monthLabels.length === 0) return;

    const { ctx } = chart;
    const xScale = chart.scales.x;
    if (!xScale) return;

    const yPos = chart.chartArea.top - 6;
    ctx.save();

    for (let i = 0; i < monthLabels.length; i++) {
      const ml = monthLabels[i];
      const leftPx = xScale.getPixelForValue(ml.start);
      const rightPx = xScale.getPixelForValue(ml.end);
      const midX = (leftPx + rightPx) / 2;

      if (i > 0) {
        const prevMl = monthLabels[i - 1];
        const prevLastPx = xScale.getPixelForValue(prevMl.end);
        const currFirstPx = xScale.getPixelForValue(ml.start);
        const sepPx = (prevLastPx + currFirstPx) / 2;
        ctx.beginPath();
        ctx.strokeStyle = "#cbd5e1";
        ctx.lineWidth = 1;
        ctx.moveTo(sepPx, yPos - 4);
        ctx.lineTo(sepPx, chart.chartArea.bottom);
        ctx.stroke();
      }

      ctx.font = "bold 13px sans-serif";
      ctx.fillStyle = "#475569";
      ctx.textAlign = "center";
      ctx.fillText(ml.label, midX, yPos);
    }

    ctx.restore();
  },
};
