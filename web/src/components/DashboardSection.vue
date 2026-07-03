<script setup lang="ts">
defineProps<{
  title: string;
  empty?: boolean;
  emptyMessage?: string;
}>();
</script>

<template>
  <section class="dashboard-section">
    <div class="dashboard-section__header">
      <h2>{{ title }}</h2>
    </div>

    <p v-if="empty" class="dashboard-section__empty">
      {{ emptyMessage ?? "Keine Daten für den gewählten Zeitraum." }}
    </p>

    <div v-else class="dashboard-section__content">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.dashboard-section {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  border: 1px solid #d8dee6;
  border-radius: 14px;
  background: #fff;
}

.dashboard-section__header h2 {
  margin: 0;
  font-size: 1.1rem;
}

.dashboard-section__empty {
  margin: 0;
  color: #5b6472;
}

.dashboard-section__content {
  min-width: 0;
}
</style>
