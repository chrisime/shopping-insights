<script setup lang="ts">
import { computed } from "vue";

import ReceiptViewer from "./ReceiptViewer.vue";
import { useReceiptBrowser } from "../composables/useReceiptBrowser";
import { fetchReceiptsByItem } from "../api/dashboard";
import { retailerLabel } from "../utils/format";
import { t } from "../utils/copy";

const props = defineProps<{
  articleName: string;
  retailer?: string;
  visible: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

const visible = computed(() => props.visible);
const { loading, receipts, currentIndex, current } = useReceiptBrowser(
  () => fetchReceiptsByItem(props.articleName, props.retailer),
  visible,
);

const title = computed(
  () =>
    `${props.articleName} — ${retailerLabel(current.value?.retailer)} ${t("receipt.receiptsTitle")}`,
);
</script>

<template>
  <ReceiptViewer
    v-model:current-index="currentIndex"
    :title="title"
    :visible="visible"
    :loading="loading"
    :receipts="receipts"
    highlight-matched
    @close="emit('close')"
  />
</template>
