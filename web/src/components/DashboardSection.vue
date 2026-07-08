<script setup lang="ts">
defineProps<{
  title: string;
  empty?: boolean;
  emptyMessage?: string;
}>();
</script>

<template>
  <section class="grid gap-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
    <div class="border-b border-slate-100 pb-3">
      <h2 class="text-lg font-semibold tracking-tight text-slate-900">{{ title }}</h2>
    </div>

    <p v-if="empty" class="text-sm text-slate-500">
      {{ emptyMessage ?? "Keine Daten für den gewählten Zeitraum." }}
    </p>

    <div v-else class="min-w-0">
      <slot />
    </div>
  </section>
</template>
