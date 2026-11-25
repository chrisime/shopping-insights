import { use } from "echarts/core";
import { BarChart } from "echarts/charts";
import { DataZoomSliderComponent, GridComponent, TooltipComponent } from "echarts/components";
import { LabelLayout } from "echarts/features";
import { SVGRenderer } from "echarts/renderers";

use([BarChart, DataZoomSliderComponent, GridComponent, TooltipComponent, LabelLayout, SVGRenderer]);
