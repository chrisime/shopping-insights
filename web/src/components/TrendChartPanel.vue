<script setup lang="ts">
defineProps<{
  items: Array<Record<string, unknown>>;
}>();

function text(value: unknown) {
  return value == null ? "-" : String(value);
}
</script>

<template>
  <ul class="panel-list">
    <li v-for="item in items" :key="text(item.period)" class="panel-list__item">
      <span>{{ text(item.period) }}</span>
      <span>{{ text(item.total_spent) }}</span>
      <span>{{ text(item.receipt_count) }} Belege</span>
    </li>
  </ul>
</template>

<style scoped>
.panel-list {
  display: grid;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.panel-list__item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 0.75rem;
  padding: 0.75rem 0.9rem;
  border-radius: 10px;
  background: #f7f9fc;
}
</style>
