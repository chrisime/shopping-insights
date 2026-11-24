<script setup lang="ts">
import { computed, ref, watch } from "vue";

import ReceiptInfo from "./ReceiptInfo.vue";
import ReceiptItems from "./ReceiptItems.vue";
import { t } from "../utils/copy";
import type { Receipt } from "../types/dashboard";

const props = defineProps<{
  title: string;
  visible: boolean;
  loading: boolean;
  error?: string | null;
  receipts: Receipt[];
  currentIndex: number;
  highlightMatched?: boolean;
}>();

const emit = defineEmits<{
  (eventName: "close"): void;
  (eventName: "update:currentIndex", value: number): void;
}>();

const current = computed<Receipt | undefined>(() => props.receipts[props.currentIndex]);

const dialog = ref<HTMLDialogElement | null>(null);

watch(
  [dialog, () => props.visible],
  ([element, visible]) => {
    if (!element) return;

    if (visible) {
      element.showModal();
    } else {
      element.close();
    }
  },
  { flush: "post" },
);
</script>

<template>
  <dialog
    ref="dialog"
    :aria-label="title"
    class="fixed inset-0 m-0 h-full max-h-none w-full max-w-none overflow-hidden overscroll-none bg-transparent p-0 backdrop:bg-black/30"
    @cancel.prevent="emit('close')"
  >
    <div
      v-if="visible"
      data-testid="receipt-overlay"
      class="flex h-full items-center justify-center p-4"
      @click.self="emit('close')"
    >
      <div
        class="flex h-150 max-h-full w-full max-w-200 flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl"
      >
        <div class="flex shrink-0 items-center justify-between border-b border-slate-200 px-5 py-4">
          <h2 class="text-lg font-semibold tracking-tight text-slate-900">{{ title }}</h2>
          <button
            type="button"
            :aria-label="t('receipt.close')"
            class="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
            @click="emit('close')"
          >
            <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path
                d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
              />
            </svg>
          </button>
        </div>

        <div v-if="loading" class="flex items-center justify-center py-16 text-sm text-slate-500">
          {{ t("receipt.loading") }}
        </div>

        <div
          v-else-if="error"
          role="alert"
          class="flex items-center justify-center py-16 text-sm text-red-700"
        >
          {{ error }}
        </div>

        <div
          v-else-if="!current"
          class="flex items-center justify-center py-16 text-sm text-slate-500"
        >
          {{ t("receipt.empty") }}
        </div>

        <template v-else>
          <div
            v-if="receipts.length > 1"
            class="flex shrink-0 items-center justify-between border-b border-slate-100 px-5 py-2.5"
          >
            <button
              type="button"
              :disabled="currentIndex <= 0"
              class="rounded-lg border border-slate-300 bg-white px-3 py-1 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              @click="emit('update:currentIndex', currentIndex - 1)"
            >
              {{ t("common.previous") }}
            </button>
            <span class="text-sm text-slate-500">
              {{ t("receipt.pagination", { current: currentIndex + 1, total: receipts.length }) }}
            </span>
            <button
              type="button"
              :disabled="currentIndex >= receipts.length - 1"
              class="rounded-lg border border-slate-300 bg-white px-3 py-1 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              data-testid="receipt-next"
              @click="emit('update:currentIndex', currentIndex + 1)"
            >
              {{ t("common.next") }}
            </button>
          </div>

          <ReceiptInfo :receipt="current" />

          <ReceiptItems :receipt="current" :highlight-matched="highlightMatched" />
        </template>
      </div>
    </div>
  </dialog>
</template>
