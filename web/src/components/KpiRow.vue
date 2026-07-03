<script setup lang="ts">
defineProps<{
  items: Array<Record<string, unknown>>;
}>();

function text(value: unknown) {
  return value == null ? "-" : String(value);
}
</script>

<template>
  <div class="kpi-row">
    <article v-for="item in items" :key="text(item.label)" class="kpi-card">
      <span class="kpi-card__label">{{ text(item.label) }}</span>
      <strong class="kpi-card__value">{{ text(item.value) }}</strong>
    </article>
  </div>
</template>

<style scoped>
.kpi-row {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
}

.kpi-card {
  display: grid;
  gap: 0.35rem;
  padding: 0.9rem;
  border-radius: 12px;
  background: #f7f9fc;
}

.kpi-card__label {
  font-size: 0.84rem;
  color: #5b6472;
}

.kpi-card__value {
  font-size: 1.15rem;
}
</style>
