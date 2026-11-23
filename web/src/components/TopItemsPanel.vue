<script setup lang="ts">
import { computed } from "vue";
import { OField, OSelect } from "@oruga-ui/oruga-next";

import { euro, quantity } from "../utils/format";
import { t } from "../utils/copy";
import type { TopItemRow } from "../types/dashboard";

const props = defineProps<{
  items: TopItemRow[];
  page: number;
  pageSize: number;
  totalCount: number;
  topLimit: number;
}>();

const emit = defineEmits<{
  (e: "update:page", value: number): void;
  (e: "update:topLimit", value: number): void;
  (e: "select-article", name: string): void;
}>();

const totalPages = computed(() => Math.max(1, Math.ceil(props.totalCount / props.pageSize)));
const rangeStart = computed(() => (props.page - 1) * props.pageSize + 1);
const rangeEnd = computed(() => Math.min(props.page * props.pageSize, props.totalCount));

function prev() {
  if (props.page > 1) emit("update:page", props.page - 1);
}

function next() {
  if (props.page < totalPages.value) emit("update:page", props.page + 1);
}
</script>

<template>
  <div class="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
    <table class="min-w-full divide-y divide-slate-200">
      <thead class="bg-slate-50">
        <tr>
          <th
            scope="col"
            class="px-4 py-3 text-left text-xs font-medium uppercase tracking-[0.22em] text-slate-500"
          >
            {{ t("common.article") }}
          </th>
          <th
            scope="col"
            class="px-4 py-3 text-right text-xs font-medium uppercase tracking-[0.22em] text-slate-500"
          >
            {{ t("common.totalQuantity") }}
          </th>
          <th
            scope="col"
            class="px-4 py-3 text-right text-xs font-medium uppercase tracking-[0.22em] text-slate-500"
          >
            {{ t("common.spending") }}
          </th>
          <th
            scope="col"
            class="px-4 py-3 text-right text-xs font-medium uppercase tracking-[0.22em] text-slate-500"
          >
            {{ t("common.purchases") }}
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-100 bg-white">
        <tr
          v-for="item in items"
          :key="item.name"
          class="cursor-pointer transition hover:bg-slate-50"
          @click="emit('select-article', item.name)"
        >
          <td class="px-4 py-3 text-sm font-medium text-slate-900">{{ item.name }}</td>
          <td class="px-4 py-3 text-right text-sm text-slate-700">
            {{ quantity(item.total_quantity, item.unit) }}
          </td>
          <td class="px-4 py-3 text-right text-sm text-slate-700">{{ euro(item.total_spent) }}</td>
          <td class="px-4 py-3 text-right text-sm text-slate-700">{{ item.purchase_count }}</td>
        </tr>
      </tbody>
    </table>

    <div
      v-if="totalCount > 0"
      class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-4 py-3"
    >
      <p class="text-sm text-slate-500">
        {{ t("filters.paginationRange", { start: rangeStart, end: rangeEnd, total: totalCount }) }}
      </p>
      <div class="flex items-center gap-3">
        <OField :label="t('filters.entriesPerPage')" class="mb-0">
          <OSelect
            :model-value="topLimit"
            expanded
            @update:model-value="emit('update:topLimit', $event)"
          >
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </OSelect>
        </OField>
        <div class="flex gap-2">
          <button
            type="button"
            :disabled="page <= 1"
            class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            @click="prev"
          >
            {{ t("filters.previousPage") }}
          </button>
          <button
            type="button"
            :disabled="page >= totalPages"
            class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            @click="next"
          >
            {{ t("filters.nextPage") }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
