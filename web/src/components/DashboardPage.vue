<script setup lang="ts">
import {computed, ref} from "vue";

import DashboardFilters from "./DashboardFilters.vue";
import DashboardSidebar from "./DashboardSidebar.vue";
import type {SidebarTab} from "./DashboardSidebar.vue";
import ImportJobControls from "./ImportJobControls.vue";
import General from "./General.vue";
import Shopping from "./Shopping.vue";
import ShoppingItems from "./ShoppingItems.vue";
import DashboardSkeleton from "./DashboardSkeleton.vue";
import SpendingOverTime from "./SpendingOverTime.vue";
import ReceiptModal from "./ReceiptModal.vue";
import ReceiptListModal from "./ReceiptListModal.vue";
import {useDashboard} from "../composables/useDashboard";
import {useImportJob} from "../composables/useImportJob";
import {useReceiptExport} from "../composables/useReceiptExport";
import {apiErrorText, t} from "../utils/copy";
import type {PeriodSelection} from "../types/chart";
import type {ImportRetailer} from "../types/imports";

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

const {exporting, exportError, exportReceipts} = useReceiptExport(() => ({
  retailer: retailer.value || undefined,
  start_date: startDate.value || undefined,
  end_date: endDate.value || undefined,
}));

const importRetailer = ref<ImportRetailer>("lidl");
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
    () => payload.value?.sections.filter((section) => section.kind === "metrics") ?? [],
);
const spendingOverTime = computed(
    () => payload.value?.sections.filter((section) => section.kind === "spending_over_time") ?? [],
);
const shoppingSections = computed(
    () => payload.value?.sections.filter((section) => section.kind === "shopping") ?? [],
);
const shoppingItems = computed(
    () => payload.value?.sections.filter((section) => section.kind === "shopping_items") ?? [],
);
</script>

<template>
  <div class="flex min-h-screen bg-slate-50">
    <DashboardSidebar v-model:activeTab="activeTab" v-model:collapsed="sidebarCollapsed"/>

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
            @click="exportReceipts"
        >
          {{ exporting ? t("dashboard.exporting") : t("dashboard.export") }}
        </button>
      </header>

      <DashboardFilters
          v-if="activeTab !== 'import'"
          v-model:retailer="retailer"
          v-model:start-date="startDate"
          v-model:end-date="endDate"
          :min-date="payload?.min_date ?? undefined"
          :max-date="payload?.max_date ?? undefined"
      />

      <p
          v-if="bannerMessage"
          class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
      >
        {{ bannerMessage }}
      </p>

      <DashboardSkeleton v-if="loading && !payload"/>

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

        <General v-else-if="activeTab === 'spending'" :sections="spendingSections"/>

        <SpendingOverTime
            v-else-if="activeTab === 'spending-over-time'"
            v-model:timeGranularity="timeGranularity"
            :sections="spendingOverTime"
            @select-period="selectedPeriod = $event"
        />

        <Shopping v-else-if="activeTab === 'shopping'" :sections="shoppingSections"/>

        <ShoppingItems
            v-else-if="activeTab === 'items'"
            v-model:search="search"
            v-model:top-view="topView"
            v-model:page="page"
            v-model:top-limit="topLimit"
            :sections="shoppingItems"
            @select-article="selectedArticle = $event"
        />
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
