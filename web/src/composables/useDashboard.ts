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
        if (!payload.value && !startDate.value && !endDate.value && response.min_date && response.max_date) {
          skipNextAutoRefresh.value = true;
          startDate.value = response.min_date;
          endDate.value = response.max_date;
        }
        payload.value = response;
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
