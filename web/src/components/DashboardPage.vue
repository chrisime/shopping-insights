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
  <main class="min-h-screen bg-slate-50 px-4 py-6 text-slate-900 sm:px-6 lg:px-8">
    <div class="mx-auto flex w-full max-w-7xl flex-col gap-5">
      <header class="space-y-2">
        <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Shopping Analyzer</p>
        <h1 class="text-3xl font-semibold tracking-tight sm:text-4xl">
          {{ payload?.title ?? "Shopping Analyzer Dashboard" }}
        </h1>
        <p class="max-w-2xl text-sm text-slate-600 sm:text-base">Read-only dashboard with filter-driven refresh.</p>
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

      <p v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {{ error }}
      </p>

      <DashboardSkeleton v-if="loading && !payload" />

      <template v-else-if="payload">
        <DashboardSection
          v-for="section in payload.sections"
          :key="`${section.kind}-${section.title}`"
          :title="section.title"
          :empty="section.items.length === 0"
        >
          <KpiRow
            v-if="section.kind === 'metrics' || section.kind === 'bonus_rewe' || section.kind === 'bonus_lidl' || section.kind === 'bonus_total'"
            :items="section.items"
          />
          <TrendChartPanel v-else-if="section.kind === 'time_series'" :items="section.items" />
          <WeekdayPanel v-else-if="section.kind === 'weekday'" :items="section.items" />
          <TopItemsPanel v-else-if="section.kind === 'top_items'" :items="section.items" />
          <pre v-else class="m-0 whitespace-pre-wrap text-sm text-slate-600">{{ section.items }}</pre>
        </DashboardSection>
      </template>
    </div>
  </main>
</template>
