<script setup lang="ts">
import { OField, OInput, OSelect } from "@oruga-ui/oruga-next";

import { t } from "../utils/copy";

defineProps<{
  minDate?: string;
  maxDate?: string;
}>();

const retailer = defineModel<string>("retailer", { required: true });
const startDate = defineModel<string>("startDate", { required: true });
const endDate = defineModel<string>("endDate", { required: true });
</script>

<template>
  <form
    class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm xl:grid-cols-3"
    @submit.prevent
  >
    <OField :label="t('filters.retailer')">
      <OSelect v-model="retailer" expanded>
        <option value="">{{ t("common.all") }}</option>
        <option value="lidl">{{ t("retailer.lidl") }}</option>
        <option value="rewe">{{ t("retailer.rewe") }}</option>
        <option value="dm">{{ t("retailer.dm") }}</option>
        <option value="rossmann">{{ t("retailer.rossmann") }}</option>
      </OSelect>
    </OField>

    <OField :label="t('filters.startDate')">
      <OInput v-model="startDate" :min="minDate" :max="maxDate" type="date" expanded />
    </OField>

    <OField :label="t('filters.endDate')">
      <OInput v-model="endDate" :min="minDate" :max="maxDate" type="date" expanded />
    </OField>
  </form>
</template>
