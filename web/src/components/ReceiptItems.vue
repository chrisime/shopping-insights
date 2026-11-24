<script setup lang="ts">
import ReceiptCouponSavings from "./ReceiptCouponSavings.vue";
import type { Receipt, ReceiptItem } from "../types/dashboard";
import { t } from "../utils/copy";
import { euro, quantity } from "../utils/format";

const props = defineProps<{
  receipt: Receipt;
  highlightMatched?: boolean;
}>();

const isMatched = (item: ReceiptItem): boolean => props.highlightMatched && item.matched === true;
</script>

<template>
  <div class="min-h-0 flex-1 overflow-y-auto overscroll-y-contain px-5 pb-4">
    <div class="border-t border-slate-200 pt-3">
      <h3 class="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        {{ t("receipt.items") }}
      </h3>
      <div class="divide-y divide-slate-100">
        <div
          v-for="(item, index) in receipt.items"
          :key="index"
          class="flex items-center justify-between gap-3 px-3 py-2 text-sm"
          :class="isMatched(item) ? '-mx-3 rounded-xl bg-amber-50 px-3 ring-1 ring-amber-300' : ''"
        >
          <div class="flex items-center gap-2">
            <span
              v-if="isMatched(item)"
              data-testid="receipt-item-match"
              class="h-2 w-2 rounded-full bg-amber-400"
            />
            <span :class="isMatched(item) ? 'font-semibold text-amber-900' : 'text-slate-700'">
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
      v-if="receipt.retailer === 'rossmann'"
      :coupons="receipt.receipt_coupons"
      :currency="receipt.currency"
    />

    <div class="mt-4 border-t border-slate-200 pt-3 text-right">
      <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">{{
        t("receipt.total")
      }}</span>
      <p class="text-xl font-semibold text-slate-900">{{ euro(receipt.total_price) }}</p>
    </div>
  </div>
</template>
