<script setup lang="ts">
import { computed } from "vue";

import ReceiptViewer from "./ReceiptViewer.vue";
import { useReceiptBrowser } from "../composables/useReceiptBrowser";
import { fetchReceiptsByDateRange } from "../api/dashboard";
import { periodLabel } from "../utils/period";

const props = defineProps<{
  startDate: string;
  endDate: string;
  visible: boolean;
  retailer?: string;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

const visible = computed(() => props.visible);
const { loading, receipts, currentIndex } = useReceiptBrowser(
  () => fetchReceiptsByDateRange(props.startDate, props.endDate, props.retailer),
  visible,
);

const title = computed(() => `${periodLabel(props.startDate, props.endDate)} — Kassenzettel`);
</script>

<template>
  <ReceiptViewer
    v-model:current-index="currentIndex"
    :title="title"
    :visible="visible"
    :loading="loading"
    :receipts="receipts"
    @close="emit('close')"
  />
</template>
