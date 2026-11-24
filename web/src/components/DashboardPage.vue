<script setup lang="ts">
import { computed, ref } from "vue";
import { OField, OInput, ORadio, OSelect } from "@oruga-ui/oruga-next";

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
import ReceiptModal from "./ReceiptModal.vue";
import ReceiptListModal from "./ReceiptListModal.vue";
import { useDashboard } from "../composables/useDashboard";
import { useImportJob } from "../composables/useImportJob";
import { exportReceiptsJson } from "../api/exports";
import { ApiRequestError } from "../api/http";
import { apiErrorText, dashboardSectionTitle, networkErrorText, t } from "../utils/copy";
import type { PeriodSelection } from "../types/chart";
import type { ImportRetailer } from "../types/imports";

const {
  retailer,
  startDate,
  endDate,
  timeGranularity,
  topView,
  topLimit,
  search,
  page,
  payload,
  loading,
  error,
  refresh,
} = useDashboard();

const {
  running: importRunning,
  progress: importProgress,
  message: importMessage,
  error: importError,
  technicalError: importTechnicalError,
  startImport,
} = useImportJob(() => refresh(true));

const importRetailer = ref<ImportRetailer>("lidl");
const exporting = ref(false);
const exportError = ref<string | null>(null);
const sidebarCollapsed = ref(false);
const activeTab = ref<SidebarTab>("spending");
const selectedArticle = ref<string | null>(null);
const selectedPeriod = ref<PeriodSelection | null>(null);

const bannerMessage = computed(() =>
  payload.value?.error
    ? apiErrorText(payload.value.error.error_code)
    : (exportError.value ?? error.value),
);

const spendingSections = computed(
  () =>
    payload.value?.sections.filter(
      (section) => section.kind === "metrics" || section.kind === "time_series",
    ) ?? [],
);
const weekdaySections = computed(
  () => payload.value?.sections.filter((section) => section.kind === "weekday") ?? [],
);
const topItemSections = computed(
  () => payload.value?.sections.filter((section) => section.kind === "top_items") ?? [],
);

async function handleExport() {
  exporting.value = true;
  exportError.value = null;
  try {
    await exportReceiptsJson({
      retailer: retailer.value || undefined,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined,
    });
  } catch (cause) {
    exportError.value =
      cause instanceof ApiRequestError
        ? cause.kind === "api"
          ? apiErrorText(cause.errorCode)
          : networkErrorText()
        : t("errors.export");
  } finally {
    exporting.value = false;
  }
}
</script>

<template>
  <div class="flex min-h-screen bg-slate-50">
    <DashboardSidebar v-model:activeTab="activeTab" v-model:collapsed="sidebarCollapsed" />

    <main class="flex min-w-0 flex-1 flex-col gap-5 px-4 py-6 text-slate-900 sm:px-6 lg:px-8">
      <header class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div class="space-y-2">
          <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
            {{ t("app.name") }}
          </p>
          <h1 class="text-3xl font-semibold tracking-tight sm:text-4xl">
            {{ t("app.title") }}
          </h1>
          <p class="max-w-2xl text-sm text-slate-600 sm:text-base">
            {{ t("app.tagline") }}
          </p>
        </div>

        <button
          type="button"
          class="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-slate-400 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="loading || exporting || !payload || !!payload.error"
          data-testid="dashboard-export"
          @click="handleExport"
        >
          {{ exporting ? t("dashboard.exporting") : t("dashboard.export") }}
        </button>
      </header>

      <form
        v-if="activeTab !== 'import'"
        class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm xl:grid-cols-3"
        @submit.prevent
      >
        <OField :label="t('filters.retailer')">
          <OSelect v-model="retailer" expanded>
            <option value="">{{ t("common.all") }}</option>
            <option value="lidl">{{ t("retailer.lidl") }}</option>
            <option value="rewe">{{ t("retailer.rewe") }}</option>
            <option value="dm">{{ t("retailer.dm") }}</option>
            <option value="rossmann">{{ t("retailer.rossmann") }}</option>
          </OSelect>
        </OField>

        <OField :label="t('filters.startDate')">
          <OInput
            v-model="startDate"
            :min="payload?.min_date ?? undefined"
            :max="payload?.max_date ?? undefined"
            type="date"
            expanded
          />
        </OField>

        <OField :label="t('filters.endDate')">
          <OInput
            v-model="endDate"
            :min="payload?.min_date ?? undefined"
            :max="payload?.max_date ?? undefined"
            type="date"
            expanded
          />
        </OField>
      </form>

      <p
        v-if="bannerMessage"
        class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
      >
        {{ bannerMessage }}
      </p>

      <DashboardSkeleton v-if="loading && !payload" />

      <template v-else-if="payload">
        <ImportJobControls
          v-if="activeTab === 'import'"
          v-model:retailer="importRetailer"
          :running="importRunning"
          :progress="importProgress"
          :message="importMessage"
          :error="importError"
          :technical-error="importTechnicalError"
          @start-import="startImport($event)"
        />

        <template v-else-if="activeTab === 'spending'">
          <DashboardSection
            v-for="section in spendingSections"
            :key="`${section.kind}-${section.title}`"
            :title="dashboardSectionTitle(section.title)"
            :empty="section.items.length === 0"
          >
            <DashboardKpiGrid v-if="section.kind === 'metrics'" :data="section.items[0] ?? {}" />
            <template v-else-if="section.kind === 'time_series'">
              <div class="mb-8">
                <label class="mb-3 block text-sm font-medium text-slate-700">{{
                  t("filters.granularity")
                }}</label>
                <div class="flex gap-4">
                  <ORadio v-model="timeGranularity" native-value="daily">{{
                    t("filters.daily")
                  }}</ORadio>
                  <ORadio v-model="timeGranularity" native-value="monthly">{{
                    t("filters.monthly")
                  }}</ORadio>
                  <ORadio v-model="timeGranularity" native-value="yearly">{{
                    t("filters.yearly")
                  }}</ORadio>
                </div>
              </div>
              <div class="mb-8">
                <TrendChartPanel
                  :items="section.items"
                  :time-granularity="timeGranularity"
                  @select-period="selectedPeriod = $event"
                />
              </div>
            </template>
          </DashboardSection>
        </template>

        <template v-else-if="activeTab === 'shopping'">
          <DashboardSection
            v-for="section in weekdaySections"
            :key="`${section.kind}-${section.title}`"
            :title="dashboardSectionTitle(section.title)"
            :empty="section.items.length === 0"
          >
            <WeekdayPanel :items="section.items" />
          </DashboardSection>
        </template>

        <template v-else-if="activeTab === 'items'">
          <DashboardFilterBar v-model:search="search" v-model:top-view="topView" class="mb-4" />
          <DashboardSection
            v-for="section in topItemSections"
            :key="`${section.kind}-${section.title}`"
            :title="dashboardSectionTitle(section.title)"
            :empty="section.items.length === 0"
          >
            <TopItemsPanel
              :items="section.items"
              :page="page"
              :page-size="section.items[0]?.page_size ?? 20"
              :total-count="section.items[0]?.total_count ?? 0"
              :top-limit="topLimit"
              @update:page="page = $event"
              @update:top-limit="topLimit = $event"
              @select-article="selectedArticle = $event"
            />
          </DashboardSection>
        </template>
      </template>
    </main>
  </div>

  <ReceiptModal
    :article-name="selectedArticle ?? ''"
    :retailer="retailer"
    :visible="!!selectedArticle"
    @close="selectedArticle = null"
  />

  <ReceiptListModal
    :start-date="selectedPeriod?.startDate ?? ''"
    :end-date="selectedPeriod?.endDate ?? ''"
    :retailer="retailer"
    :visible="!!selectedPeriod"
    @close="selectedPeriod = null"
  />
</template>
