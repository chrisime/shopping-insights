<script setup lang="ts">
import DashboardSection from "./DashboardSection.vue";
import DashboardFilterBar from "./DashboardFilterBar.vue";
import TopItemsPanel from "./TopItemsPanel.vue";
import type { DashboardSection as DashboardSectionData } from "../types/dashboard";
import { dashboardSectionTitle } from "../utils/copy";

defineProps<{
  sections: Extract<DashboardSectionData, { kind: "shopping_items" }>[];
}>();

const search = defineModel<string>("search", { required: true });
const topView = defineModel<string>("topView", { required: true });
const page = defineModel<number>("page", { required: true });
const topLimit = defineModel<number>("topLimit", { required: true });

const emit = defineEmits<{
  (e: "select-article", name: string): void;
}>();
</script>

<template>
  <DashboardFilterBar v-model:search="search" v-model:top-view="topView" class="mb-4" />
  <DashboardSection
    v-for="section in sections"
    :key="`${section.kind}-${section.title}`"
    :title="dashboardSectionTitle(section.title)"
    :empty="section.items.length === 0"
  >
    <TopItemsPanel
      :items="section.items"
      v-model:page="page"
      :page-size="section.items[0]?.page_size ?? 20"
      :total-count="section.items[0]?.total_count ?? 0"
      v-model:top-limit="topLimit"
      @select-article="emit('select-article', $event)"
    />
  </DashboardSection>
</template>
