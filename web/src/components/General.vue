<script setup lang="ts">
import DashboardSection from "./DashboardSection.vue";
import DashboardKpiGrid from "./DashboardKpiGrid.vue";
import type { DashboardSection as DashboardSectionData } from "../types/dashboard";
import { dashboardSectionTitle } from "../utils/copy";

defineProps<{
  sections: Extract<DashboardSectionData, { kind: "metrics" }>[];
}>();
</script>

<template>
  <DashboardSection
    v-for="section in sections"
    :key="`${section.kind}-${section.title}`"
    :title="dashboardSectionTitle(section.title)"
    :empty="section.items.length === 0"
  >
    <DashboardKpiGrid :data="section.items[0] ?? {}" />
  </DashboardSection>
</template>
