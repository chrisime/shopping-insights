<script setup lang="ts">
defineProps<{
  items: Array<Record<string, unknown>>;
}>();

function text(value: unknown) {
  return value == null ? "-" : String(value);
}
</script>

<template>
  <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
    <article
      v-for="item in items"
      :key="text(item.label)"
      class="grid gap-1 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 shadow-sm ring-1 ring-slate-100/70"
    >
      <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">{{ text(item.label) }}</span>
      <strong class="text-2xl font-semibold tracking-tight text-slate-900">{{ text(item.value) }}</strong>
    </article>
  </div>
</template>
