import { ref } from "vue";

import { exportReceiptsJson } from "../api/exports";
import { ApiRequestError } from "../api/http";
import type { DashboardFilters } from "../types/dashboard";
import { apiErrorText, networkErrorText, t } from "../utils/copy";

export function useReceiptExport(getFilters: () => DashboardFilters) {
  const exporting = ref(false);
  const exportError = ref<string | null>(null);

  async function exportReceipts() {
    exporting.value = true;
    exportError.value = null;
    try {
      await exportReceiptsJson(getFilters());
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

  return { exporting, exportError, exportReceipts };
}
