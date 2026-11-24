<script setup lang="ts">
import DashboardSection from "./DashboardSection.vue";
import WeekdayPanel from "./WeekdayPanel.vue";
import type { DashboardSection as DashboardSectionData } from "../types/dashboard";
import { dashboardSectionTitle } from "../utils/copy";

defineProps<{
  sections: Extract<DashboardSectionData, { kind: "shopping" }>[];
}>();
</script>

<template>
  <DashboardSection
    v-for="section in sections"
    :key="`${section.kind}-${section.title}`"
    :title="dashboardSectionTitle(section.title)"
    :empty="section.items.length === 0"
  >
    <WeekdayPanel :items="section.items" />
  </DashboardSection>
</template>
