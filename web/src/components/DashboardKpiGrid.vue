<script setup lang="ts">
import { computed } from "vue";

import { euro, percentage } from "../utils/format";
import { t } from "../utils/copy";
import { GENERAL_KPI_GROUPS, KPI_FIELD_LABELS, visibleRetailerDiscounts } from "../utils/kpiCards";
import type { MetricsRow } from "../types/dashboard";

const props = defineProps<{
  data: MetricsRow;
}>();

const formatValue = (key: string, value: number): string => {
  if (key.endsWith("_pct")) {
    return percentage(value);
  }
  if (key === "receipt_count") {
    return String(value);
  }
  return euro(value);
};

const retailerDiscounts = computed(() => visibleRetailerDiscounts(props.data));
</script>

<template>
  <div class="grid gap-4">
    <div
      v-for="group in data.spendings === undefined ? [] : GENERAL_KPI_GROUPS"
      :key="group[0].title"
      class="grid gap-3 lg:grid-cols-2"
    >
      <article
        v-for="card in group"
        :key="card.title"
        :data-testid="`kpi-card-${card.fields[0]}`"
        class="grid gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 shadow-sm ring-1 ring-slate-100/70"
      >
        <div class="border-b border-slate-200/70 pb-2">
          <h3 class="text-sm font-semibold tracking-tight text-slate-900">{{ card.title }}</h3>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div
            v-for="(field, index) in card.fields"
            :key="field"
            data-testid="kpi-field"
            class="grid gap-1"
            :class="index === 1 ? 'justify-items-end text-right' : ''"
          >
            <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">{{
              KPI_FIELD_LABELS[field] ?? field
            }}</span>
            <strong class="text-2xl font-semibold tracking-tight text-slate-900">{{
              formatValue(field, data[field])
            }}</strong>
          </div>
        </div>
      </article>
    </div>
    <div v-if="retailerDiscounts.length" class="grid gap-4 md:grid-cols-2">
      <article
        v-for="retailer in retailerDiscounts"
        :key="retailer.name"
        class="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
      >
        <header class="bg-slate-50 px-4 py-4 sm:px-5">
          <h3 class="text-base font-semibold text-slate-900">{{ retailer.name }}</h3>
          <dl class="mt-3 flex flex-wrap items-end justify-between gap-x-4 gap-y-2">
            <div>
              <dt class="text-xs font-medium text-slate-600">{{ t("common.totalSavings") }}</dt>
              <dd class="text-2xl font-semibold tracking-tight text-slate-900 tabular-nums">
                {{ euro(retailer.amount) }}
              </dd>
            </div>
            <div class="text-right">
              <dt class="text-xs font-medium text-slate-600">{{ t("kpi.savingsRate") }}</dt>
              <dd class="text-xl font-semibold text-slate-900 tabular-nums">
                {{ percentage(retailer.rate) }}
              </dd>
            </div>
          </dl>
        </header>

        <div
          v-if="retailer.details.length"
          class="divide-y divide-slate-100 border-t border-slate-200 px-4 sm:px-5"
        >
          <div v-for="detail in retailer.details" :key="detail.title" class="py-2.5">
            <div class="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
              <h4 class="text-sm font-medium text-slate-800">{{ detail.title }}</h4>
              <dl
                class="gap-x-4 gap-y-1"
                :class="
                  detail.supportingFields
                    ? 'grid grid-cols-[auto_auto] text-right'
                    : 'flex flex-wrap'
                "
              >
                <div
                  v-for="field in detail.fields"
                  :key="field"
                  class="flex items-baseline gap-x-1.5"
                  :class="detail.supportingFields ? 'justify-end' : ''"
                >
                  <dt
                    :class="
                      detail.supportingFields && !field.endsWith('_pct')
                        ? 'text-xs text-slate-600'
                        : 'sr-only'
                    "
                  >
                    {{ KPI_FIELD_LABELS[field] }}
                  </dt>
                  <dd class="text-sm font-medium text-slate-900 tabular-nums">
                    {{ formatValue(field, data[field]) }}
                  </dd>
                </div>
                <template
                  v-if="detail.supportingFields?.every((field) => data[field] !== undefined)"
                >
                  <div
                    v-for="field in detail.supportingFields"
                    :key="field"
                    class="col-start-1 flex items-baseline justify-end gap-x-1.5 whitespace-nowrap text-xs"
                  >
                    <dt class="text-slate-600">{{ KPI_FIELD_LABELS[field] }}</dt>
                    <dd class="font-medium text-slate-800 tabular-nums">
                      {{ formatValue(field, data[field]) }}
                    </dd>
                  </div>
                </template>
              </dl>
            </div>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
