<script setup lang="ts">
import { ORadio } from "@oruga-ui/oruga-next";

import DashboardSection from "./DashboardSection.vue";
import TrendChartPanel from "./TrendChartPanel.vue";
import type { PeriodSelection } from "../types/chart";
import type { DashboardSection as DashboardSectionData } from "../types/dashboard";
import { dashboardSectionTitle, t } from "../utils/copy";

defineProps<{
  sections: Extract<DashboardSectionData, { kind: "spending_over_time" }>[];
}>();

const timeGranularity = defineModel<"daily" | "monthly" | "yearly">("timeGranularity", {
  required: true,
});

const emit = defineEmits<{
  (e: "select-period", payload: PeriodSelection): void;
}>();
</script>

<template>
  <DashboardSection
    v-for="section in sections"
    :key="`${section.kind}-${section.title}`"
    :title="dashboardSectionTitle(section.title)"
    :empty="section.items.length === 0"
  >
    <div class="mb-8">
      <label class="mb-3 block text-sm font-medium text-slate-700">{{
        t("filters.granularity")
      }}</label>
      <div class="flex gap-4">
        <ORadio v-model="timeGranularity" native-value="daily">{{ t("filters.daily") }}</ORadio>
        <ORadio v-model="timeGranularity" native-value="monthly">{{ t("filters.monthly") }}</ORadio>
        <ORadio v-model="timeGranularity" native-value="yearly">{{ t("filters.yearly") }}</ORadio>
      </div>
    </div>
    <div class="mb-8">
      <TrendChartPanel
        :items="section.items"
        :time-granularity="timeGranularity"
        @select-period="emit('select-period', $event)"
      />
    </div>
  </DashboardSection>
</template>
