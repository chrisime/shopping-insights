<script setup lang="ts">
import { computed, ref } from "vue";

import { OField, OInput, OSelect } from "@oruga-ui/oruga-next";

import DashboardSidebar from "./DashboardSidebar.vue";
import type { SidebarTab } from "./DashboardSidebar.vue";
import DashboardFilterBar from "./DashboardFilterBar.vue";
import ImportJobControls from "./ImportJobControls.vue";
import DashboardSection from "./DashboardSection.vue";
import DashboardSkeleton from "./DashboardSkeleton.vue";
import DashboardKpiGrid from "./DashboardKpiGrid.vue";
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
  search,
  page,
  payload,
  loading,
  error,
  refresh,
} = useDashboard();

const importRetailer = ref<ImportRetailer>("lidl");
const importJob = useImportJob(refresh);

const exporting = ref(false);
const sidebarCollapsed = ref(false);
const activeTab = ref<SidebarTab>("ausgaben");

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

function metricData(items: Array<Record<string, unknown>>): Record<string, number> {
  return items.length ? (items[0] as Record<string, number>) : {};
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
  <div class="flex min-h-screen bg-slate-50">
    <DashboardSidebar
      :active-tab="activeTab"
      :collapsed="sidebarCollapsed"
      @update:active-tab="activeTab = $event"
      @update:collapsed="sidebarCollapsed = $event"
    />

    <main class="flex min-w-0 flex-1 flex-col gap-5 px-4 py-6 text-slate-900 sm:px-6 lg:px-8">
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

      <form class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm xl:grid-cols-3" @submit.prevent>
        <OField label="Händler">
          <OSelect v-model="retailer" expanded>
            <option value="">Alle</option>
            <option value="lidl">Lidl</option>
            <option value="rewe">REWE</option>
          </OSelect>
        </OField>

        <OField label="Startdatum">
          <OInput v-model="startDate" :min="(payload?.min_date ?? undefined) as any" :max="(payload?.max_date ?? undefined) as any" type="date" expanded />
        </OField>

        <OField label="Enddatum">
          <OInput v-model="endDate" :min="(payload?.min_date ?? undefined) as any" :max="(payload?.max_date ?? undefined) as any" type="date" expanded />
        </OField>

        <OField label="Zeitgranularität">
          <OSelect v-model="timeGranularity" expanded>
            <option>Täglich</option>
            <option>Monatlich</option>
            <option>Jährlich</option>
          </OSelect>
        </OField>

        <OField label="Ansicht">
          <OSelect v-model="spendingView" expanded>
            <option>Absolut</option>
            <option>Kumulativ</option>
          </OSelect>
        </OField>

        <OField label="Sortieren nach">
          <OSelect v-model="topView" expanded>
            <option>Menge</option>
            <option>Ausgaben</option>
          </OSelect>
        </OField>
      </form>

      <p v-if="bannerMessage" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {{ bannerMessage }}
      </p>

      <DashboardSkeleton v-if="loading && !payload" />

      <template v-else-if="payload">
        <template v-if="activeTab === 'import'">
          <ImportJobControls
            v-model:retailer="importRetailer"
            :running="importJob.running.value"
            :progress="importJob.progress.value"
            :message="importJob.message.value"
            :error="importJob.error.value"
            :technical-error="importJob.technicalError.value"
            @start-import="importJob.startImport($event)"
          />
        </template>

        <template v-else-if="activeTab === 'ausgaben'">
          <DashboardSection
            v-for="section in payload.sections.filter(s => s.kind === 'metrics' || s.kind === 'time_series')"
            :key="`${section.kind}-${section.title}`"
            :title="section.title"
            :empty="section.items.length === 0"
          >
            <DashboardKpiGrid v-if="section.kind === 'metrics'" :data="metricData(section.items)" />
            <TrendChartPanel
              v-else-if="section.kind === 'time_series'"
              :items="section.items"
              :spending-view="spendingView"
              :time-granularity="timeGranularity"
            />
          </DashboardSection>
        </template>

        <template v-else-if="activeTab === 'einkauf'">
          <DashboardSection
            v-for="section in payload.sections.filter(s => s.kind === 'weekday')"
            :key="`${section.kind}-${section.title}`"
            :title="section.title"
            :empty="section.items.length === 0"
          >
            <WeekdayPanel :items="section.items" />
          </DashboardSection>
        </template>

        <template v-else-if="activeTab === 'artikel'">
          <DashboardFilterBar
            v-model:search="search"
            v-model:top-limit="topLimit"
            class="mb-4"
          />
          <DashboardSection
            v-for="section in payload.sections.filter(s => s.kind === 'top_items')"
            :key="`${section.kind}-${section.title}`"
            :title="section.title"
            :empty="section.items.length === 0"
          >
            <TopItemsPanel
              :items="section.items"
              :page="page"
              :page-size="(section.items[0] as any)?.page_size ?? 20"
              :total-count="(section.items[0] as any)?.total_count ?? 0"
              @update:page="page = $event"
            />
          </DashboardSection>
        </template>
      </template>
    </main>
  </div>
</template>
