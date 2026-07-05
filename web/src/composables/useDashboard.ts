import { computed, getCurrentInstance, onMounted, onServerPrefetch, ref, watch } from "vue";

import { fetchDashboard } from "../api/dashboard";
import type { DashboardPayload } from "../types/dashboard";

export function useDashboard() {
  const retailer = ref("");
  const startDate = ref("");
  const endDate = ref("");
  const timeGranularity = ref("Täglich");
  const spendingView = ref("Absolut");
  const topView = ref("Menge");
  const topLimit = ref(20);

  const payload = ref<DashboardPayload | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const skipNextAutoRefresh = ref(false);
  const pendingDateRangeReset = ref(false);
  let requestToken = 0;

  const filters = computed(() => ({
    retailer: retailer.value || undefined,
    start_date: startDate.value || undefined,
    end_date: endDate.value || undefined,
    time_granularity: timeGranularity.value,
    spending_view: spendingView.value,
    top_view: topView.value,
    top_limit: topLimit.value,
  }));

  async function refresh() {
    const token = ++requestToken;
    loading.value = true;
    error.value = null;

    try {
      const response = await fetchDashboard(filters.value);
      if (token === requestToken) {
        payload.value = response;
        if (
          response.min_date &&
          response.max_date &&
          (pendingDateRangeReset.value || (!startDate.value && !endDate.value))
        ) {
          pendingDateRangeReset.value = false;
          syncDateRange(response.min_date, response.max_date);
        }
      }
    } catch (cause) {
      if (token === requestToken) {
        error.value = cause instanceof Error ? cause.message : "Failed to load dashboard";
      }
    } finally {
      if (token === requestToken) {
        loading.value = false;
      }
    }
  }

  watch([retailer, startDate, endDate, timeGranularity, spendingView, topView, topLimit], () => {
    if (skipNextAutoRefresh.value) {
      skipNextAutoRefresh.value = false;
      return;
    }
    void refresh();
  });

  watch(
    retailer,
    (next, previous) => {
      if (!payload.value || next === previous) {
        return;
      }

      pendingDateRangeReset.value = true;
      skipNextAutoRefresh.value = true;
      startDate.value = "";
      endDate.value = "";
      void refresh();
    },
    { flush: "sync" },
  );

  function syncDateRange(minDate: string, maxDate: string) {
    if (startDate.value === minDate && endDate.value === maxDate) {
      return;
    }

    skipNextAutoRefresh.value = true;
    startDate.value = minDate;
    endDate.value = maxDate;
  }

  if (getCurrentInstance()) {
    onMounted(() => {
      if (!payload.value && !loading.value) {
        void refresh();
      }
    });

    onServerPrefetch(refresh);
  }

  return {
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
  };
}
