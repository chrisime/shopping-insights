<script setup lang="ts">
import { computed } from "vue";

import ReceiptViewer from "./ReceiptViewer.vue";
import { useReceiptBrowser } from "../composables/useReceiptBrowser";
import { fetchReceiptsByDateRange } from "../api/dashboard";
import { periodLabel } from "../utils/period";
import { t } from "../utils/copy";

const props = defineProps<{
  startDate: string;
  endDate: string;
  visible: boolean;
  retailer?: string;
}>();

const emit = defineEmits<{
  (eventName: "close"): void;
}>();

const visible = computed(() => props.visible);
const { loading, error, receipts, currentIndex } = useReceiptBrowser(
  () => fetchReceiptsByDateRange(props.startDate, props.endDate, props.retailer),
  visible,
);

const title = computed(
  () => `${periodLabel(props.startDate, props.endDate)} — ${t("receipt.receiptsTitle")}`,
);
</script>

<template>
  <ReceiptViewer
    v-model:current-index="currentIndex"
    :title="title"
    :visible="visible"
    :loading="loading"
    :error="error"
    :receipts="receipts"
    @close="emit('close')"
  />
</template>
