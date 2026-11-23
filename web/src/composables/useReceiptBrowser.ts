import { computed, ref, watch, type Ref } from "vue";

import type { Receipt } from "../types/dashboard";

/**
 * Loads receipts whenever the modal becomes visible and keeps track of the
 * receipt shown in the pager. Stale responses are discarded via a request ticket.
 */
export function useReceiptBrowser(load: () => Promise<Receipt[]>, visible: Ref<boolean>) {
  const loading = ref(false);
  const error = ref<string | null>(null);
  const receipts = ref<Receipt[]>([]);
  const currentIndex = ref(0);
  let ticket = 0;

  watch(visible, async (show) => {
    if (!show) return;

    const request = ++ticket;
    loading.value = true;
    error.value = null;
    receipts.value = [];
    currentIndex.value = 0;

    try {
      const result = await load();
      if (request === ticket) receipts.value = result;
    } catch {
      if (request === ticket) {
        receipts.value = [];
        error.value = "Failed to load receipts";
      }
    } finally {
      if (request === ticket) loading.value = false;
    }
  });

  const current = computed<Receipt | undefined>(() => receipts.value[currentIndex.value]);

  function prev() {
    if (currentIndex.value > 0) currentIndex.value -= 1;
  }

  function next() {
    if (currentIndex.value < receipts.value.length - 1) currentIndex.value += 1;
  }

  return { loading, error, receipts, currentIndex, current, prev, next };
}
