<script setup lang="ts">
import { computed } from "vue";

import ReceiptCouponSavings from "./ReceiptCouponSavings.vue";
import { addressText, euro, quantity, retailerLabel, text } from "../utils/format";
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

function isMatched(item: Receipt["items"][number]): boolean {
  return props.highlightMatched && item.matched === true;
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      data-testid="receipt-overlay"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      @click.self="emit('close')"
    >
      <div
        class="flex max-h-[85vh] w-full max-w-2xl flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl"
      >
        <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
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
            class="flex items-center justify-between border-b border-slate-100 px-5 py-2.5"
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

          <div class="overflow-y-auto px-5 py-4">
            <div class="mb-4 grid grid-cols-4 gap-3 text-sm">
              <div>
                <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">
                  {{ t("common.retailer") }}
                </p>
                <p class="mt-0.5 font-bold uppercase text-slate-900">
                  {{ retailerLabel(current.retailer) }}
                </p>
              </div>
              <div>
                <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">
                  {{ t("receipt.market") }}
                </p>
                <p class="mt-0.5 font-medium text-slate-900">{{ text(current.store) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">
                  {{ t("receipt.address") }}
                </p>
                <p class="mt-0.5 text-xs text-slate-500">{{ addressText(current.address) }}</p>
              </div>
              <div class="text-right">
                <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">
                  {{ t("receipt.date") }}
                </p>
                <p class="mt-0.5 font-medium text-slate-900">{{ text(current.purchase_date) }}</p>
              </div>
            </div>

            <div class="border-t border-slate-200 pt-3">
              <h3 class="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                {{ t("receipt.items") }}
              </h3>
              <div class="divide-y divide-slate-100">
                <div
                  v-for="(item, index) in current.items"
                  :key="index"
                  class="flex items-center justify-between gap-3 px-3 py-2 text-sm"
                  :class="
                    isMatched(item) ? '-mx-3 rounded-xl bg-amber-50 px-3 ring-1 ring-amber-300' : ''
                  "
                >
                  <div class="flex items-center gap-2">
                    <span
                      v-if="isMatched(item)"
                      data-testid="receipt-item-match"
                      class="h-2 w-2 rounded-full bg-amber-400"
                    />
                    <span
                      :class="isMatched(item) ? 'font-semibold text-amber-900' : 'text-slate-700'"
                    >
                      {{ item.name }}
                    </span>
                  </div>
                  <span class="shrink-0 text-slate-600">
                    {{ quantity(item.quantity, item.unit) }} ×
                    {{ euro(item.price) }}
                  </span>
                </div>
              </div>
            </div>

            <ReceiptCouponSavings
              v-if="current.retailer === 'rossmann'"
              :coupons="current.receipt_coupons"
              :currency="current.currency"
            />

            <div class="mt-4 border-t border-slate-200 pt-3 text-right">
              <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">{{
                t("receipt.total")
              }}</span>
              <p class="text-xl font-semibold text-slate-900">{{ euro(current.total_price) }}</p>
            </div>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>
