<script setup lang="ts">
import { computed } from "vue";

import { euro } from "../utils/format";
import type { ReceiptCoupon } from "../types/dashboard";

const props = defineProps<{
  coupons?: ReceiptCoupon[];
  currency?: string;
}>();

const rows = computed(() => props.coupons ?? []);
</script>

<template>
  <section v-if="rows.length" class="mt-4 border-t border-slate-200 pt-3">
    <h3 class="mb-2 text-sm font-semibold text-slate-900">Deine Coupon-Ersparnis heute</h3>
    <dl class="divide-y divide-slate-100 rounded-lg border border-slate-200">
      <div
        v-for="(coupon, index) in rows"
        :key="index"
        class="flex justify-between gap-3 px-3 py-2 text-sm"
      >
        <dt>{{ coupon.name }}</dt>
        <dd class="shrink-0 font-medium tabular-nums">{{ euro(coupon.savings, currency) }}</dd>
      </div>
    </dl>
  </section>
</template>
