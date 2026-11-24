<script setup lang="ts">
import type { Receipt } from "../types/dashboard";
import { t } from "../utils/copy";
import { addressText, retailerLabel, text } from "../utils/format";

defineProps<{
  receipt: Receipt;
}>();
</script>

<template>
  <div class="grid shrink-0 grid-cols-4 gap-3 px-5 pt-4 pb-4 text-sm">
    <div>
      <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">
        {{ t("common.retailer") }}
      </p>
      <p class="mt-0.5 font-bold uppercase text-slate-900">
        {{ retailerLabel(receipt.retailer) }}
      </p>
    </div>
    <div>
      <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">
        {{ t("receipt.market") }}
      </p>
      <p class="mt-0.5 font-medium text-slate-900">{{ text(receipt.store) }}</p>
    </div>
    <div>
      <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">
        {{ t("receipt.address") }}
      </p>
      <p class="mt-0.5 text-xs text-slate-500">{{ addressText(receipt.address) }}</p>
    </div>
    <div class="text-right">
      <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">
        {{ t("receipt.date") }}
      </p>
      <p class="mt-0.5 font-medium text-slate-900">{{ text(receipt.purchase_date) }}</p>
    </div>
  </div>
</template>
