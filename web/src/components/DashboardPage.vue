<script setup lang="ts">
import DashboardFilterBar from "./DashboardFilterBar.vue";
import DashboardSection from "./DashboardSection.vue";
import DashboardSkeleton from "./DashboardSkeleton.vue";
import KpiRow from "./KpiRow.vue";
import TopItemsPanel from "./TopItemsPanel.vue";
import TrendChartPanel from "./TrendChartPanel.vue";
import WeekdayPanel from "./WeekdayPanel.vue";
import { useDashboard } from "../composables/useDashboard";

const {
  retailer,
  startDate,
  endDate,
  timeGranularity,
  spendingView,
  topView,
  topLimit,
  payload,
  loading,
  error,
} = useDashboard();
</script>

<template>
  <main class="dashboard-page">
    <header class="dashboard-page__header">
      <h1>{{ payload?.title ?? "Shopping Analyzer Dashboard" }}</h1>
      <p>Read-only dashboard with filter-driven refresh.</p>
    </header>

    <DashboardFilterBar
      v-model:retailer="retailer"
      v-model:start-date="startDate"
      v-model:end-date="endDate"
      v-model:time-granularity="timeGranularity"
      v-model:spending-view="spendingView"
      v-model:top-view="topView"
      v-model:top-limit="topLimit"
    />

    <p v-if="error" class="dashboard-page__error">{{ error }}</p>

    <DashboardSkeleton v-if="loading && !payload" />

    <template v-else-if="payload">
      <DashboardSection
        v-for="section in payload.sections"
        :key="`${section.kind}-${section.title}`"
        :title="section.title"
        :empty="section.items.length === 0"
      >
        <KpiRow v-if="section.kind === 'metrics'" :items="section.items" />
        <TrendChartPanel v-else-if="section.kind === 'time_series'" :items="section.items" />
        <WeekdayPanel v-else-if="section.kind === 'weekday'" :items="section.items" />
        <TopItemsPanel v-else-if="section.kind === 'top_items'" :items="section.items" />
        <pre v-else class="dashboard-page__fallback">{{ section.items }}</pre>
      </DashboardSection>
    </template>
  </main>
</template>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 1.25rem;
  padding: 1.5rem;
}

.dashboard-page__header h1 {
  margin: 0;
  font-size: 1.8rem;
}

.dashboard-page__header p,
.dashboard-page__error {
  margin: 0;
  color: #5b6472;
}

.dashboard-page__error {
  color: #a32a2a;
}

.dashboard-page__fallback {
  margin: 0;
  white-space: pre-wrap;
}
</style>
