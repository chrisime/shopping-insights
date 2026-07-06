<script setup lang="ts">
import { computed, ref } from "vue";

import DashboardFilterBar from "./DashboardFilterBar.vue";
import ImportJobControls from "./ImportJobControls.vue";
import DashboardSection from "./DashboardSection.vue";
import DashboardSkeleton from "./DashboardSkeleton.vue";
import KpiRow from "./KpiRow.vue";
import TopItemsPanel from "./TopItemsPanel.vue";
import TrendChartPanel from "./TrendChartPanel.vue";
import WeekdayPanel from "./WeekdayPanel.vue";
import { useDashboard } from "../composables/useDashboard";
import { exportReceiptsJson } from "../api/exports";
import { useImportJob } from "../composables/useImportJob";
import type { ImportRetailer } from "../types/imports";

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
  refresh,
} = useDashboard();

const importRetailer = ref<ImportRetailer>("lidl");
const importJob = useImportJob(refresh);

const exporting = ref(false);

const bannerMessage = computed(() => {
  if (payload.value?.error) {
    return dashboardErrorMessage(payload.value.error.detail);
  }

  return error.value;
});

function dashboardErrorMessage(detail: string) {
  if (detail === "no_receipts") {
    return "No receipts yet. Import or fetch receipts to see dashboard data.";
  }

  return "Dashboard data is unavailable. Import receipts to initialize the dashboard.";
}

async function handleExport() {
  exporting.value = true;
  try {
    await exportReceiptsJson({
      retailer: retailer.value || undefined,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined,
    });
  } finally {
    exporting.value = false;
  }
}
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-6 text-slate-900 sm:px-6 lg:px-8">
    <div class="mx-auto flex w-full max-w-7xl flex-col gap-5">
      <header class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div class="space-y-2">
          <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Shopping Analyzer</p>
          <h1 class="text-3xl font-semibold tracking-tight sm:text-4xl">
            {{ payload?.title ?? "Shopping Analyzer Dashboard" }}
          </h1>
          <p class="max-w-2xl text-sm text-slate-600 sm:text-base">Read-only dashboard with filter-driven refresh.</p>
        </div>

        <button
          type="button"
          class="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-slate-400 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="loading || exporting || !payload || !!payload.error"
          @click="handleExport"
        >
          {{ exporting ? "Exportiere JSON..." : "JSON exportieren" }}
        </button>
      </header>

      <ImportJobControls
        v-model:retailer="importRetailer"
        :running="importJob.running.value"
        :progress="importJob.progress.value"
        :message="null"
        :error="importJob.error.value"
        @start-import="importJob.startImport(importRetailer)"
      />

      <DashboardFilterBar
        v-model:retailer="retailer"
        v-model:start-date="startDate"
        v-model:end-date="endDate"
        :min-date="payload?.min_date ?? undefined"
        :max-date="payload?.max_date ?? undefined"
        v-model:time-granularity="timeGranularity"
        v-model:spending-view="spendingView"
        v-model:top-view="topView"
        v-model:top-limit="topLimit"
      />

      <p v-if="bannerMessage" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {{ bannerMessage }}
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
          <TrendChartPanel v-else-if="section.kind === 'time_series'" :items="section.items" :spending-view="spendingView" />
          <WeekdayPanel v-else-if="section.kind === 'weekday'" :items="section.items" />
          <TopItemsPanel v-else-if="section.kind === 'top_items'" :items="section.items" />
          <pre v-else class="m-0 whitespace-pre-wrap text-sm text-slate-600">{{ section.items }}</pre>
        </DashboardSection>
      </template>
    </div>
  </main>
</template>
