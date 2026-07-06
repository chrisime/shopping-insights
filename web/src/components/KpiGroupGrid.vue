<script setup lang="ts">
import type { DashboardKpiGroup } from "../types/dashboard";

defineProps<{
  groups: DashboardKpiGroup[];
}>();

function text(value: unknown) {
  return value == null ? "-" : String(value);
}

function alignRight(label: unknown) {
  return ["Sparquote", "Guthaben", "Offen"].includes(text(label));
}
</script>

<template>
  <div class="grid gap-4">
    <div
      v-for="group in groups"
      :key="`${group.layout}-${group.cards.map((card) => card.title).join('-')}`"
      class="grid gap-3"
      :class="group.layout === 'triple' ? 'lg:grid-cols-3' : group.layout === 'pair' ? 'lg:grid-cols-2' : ''"
    >
      <article
        v-for="card in group.cards"
        :key="card.title"
        class="grid gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 shadow-sm ring-1 ring-slate-100/70"
      >
        <div class="border-b border-slate-200/70 pb-2">
          <h3 class="text-sm font-semibold tracking-tight text-slate-900">{{ card.title }}</h3>
        </div>

        <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div
            v-for="item in card.items"
            :key="text(item.label)"
            class="grid gap-1"
            :class="alignRight(item.label) ? 'justify-items-end text-right' : ''"
          >
            <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">{{ text(item.label) }}</span>
            <strong class="text-2xl font-semibold tracking-tight text-slate-900">{{ text(item.value) }}</strong>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
