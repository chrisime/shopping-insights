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
    <li v-for="item in items" :key="text(item.weekday_name ?? item.weekday)" class="weekday-item">
      <span>{{ text(item.weekday_name ?? item.weekday) }}</span>
      <span>{{ text(item.trip_count) }} Einkäufe</span>
      <span>Ø {{ text(item.avg_spent) }}</span>
      <span>{{ text(item.total_spent) }}</span>
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

.weekday-item {
  display: grid;
  grid-template-columns: 1.2fr 1fr 0.8fr 0.8fr;
  gap: 0.75rem;
  padding: 0.75rem 0.9rem;
  border-radius: 10px;
  background: #f7f9fc;
}
</style>
