<script setup lang="ts">
import { OField, OInput, OSelect } from "@oruga-ui/oruga-next";
import { t } from "../utils/copy";

const search = defineModel<string>("search", { default: "" });
const topView = defineModel<string>("topView", { default: "Menge" });
</script>

<template>
  <form
    data-testid="dashboard-filter-form"
    class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
    @submit.prevent
  >
    <h2 class="text-lg font-semibold tracking-tight text-slate-900">
      {{ t("filters.itemTitle") }}
    </h2>
    <div class="grid gap-4 sm:grid-cols-2">
      <OField data-testid="dashboard-search-field" :label="t('filters.searchLabel')">
        <OInput
          data-testid="dashboard-search"
          v-model="search"
          :placeholder="t('filters.searchPlaceholder')"
          expanded
        />
      </OField>

      <OField :label="t('filters.sortBy')">
        <OSelect data-testid="dashboard-sort" v-model="topView" expanded>
          <option value="Menge">{{ t("filters.quantity") }}</option>
          <option value="Ausgaben">{{ t("filters.spending") }}</option>
        </OSelect>
      </OField>
    </div>
  </form>
</template>
