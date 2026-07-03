<script setup lang="ts">
defineProps<{
  items: Array<Record<string, unknown>>;
}>();

function text(value: unknown) {
  return value == null ? "-" : String(value);
}
</script>

<template>
  <ol class="panel-list">
    <li v-for="item in items" :key="text(item.name)" class="top-item">
      <span>{{ text(item.name) }}</span>
      <span>{{ text(item.total_quantity) }}</span>
      <span>{{ text(item.total_spent) }}</span>
      <span>{{ text(item.purchase_count) }}</span>
      <span>{{ text(item.unit) }}</span>
    </li>
  </ol>
</template>

<style scoped>
.panel-list {
  display: grid;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.top-item {
  display: grid;
  grid-template-columns: 1.5fr repeat(4, auto);
  gap: 0.75rem;
  padding: 0.75rem 0.9rem;
  border-radius: 10px;
  background: #f7f9fc;
}
</style>
