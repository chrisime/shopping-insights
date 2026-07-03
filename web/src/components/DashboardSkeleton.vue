<template>
  <div class="dashboard-skeleton" aria-hidden="true">
    <div class="dashboard-skeleton__block dashboard-skeleton__block--wide"></div>
    <div class="dashboard-skeleton__block"></div>
    <div class="dashboard-skeleton__block"></div>
    <div class="dashboard-skeleton__block"></div>
  </div>
</template>

<style scoped>
.dashboard-skeleton {
  display: grid;
  gap: 0.75rem;
}

.dashboard-skeleton__block {
  height: 92px;
  border-radius: 14px;
  background: linear-gradient(90deg, #eff3f8 25%, #e6ebf2 37%, #eff3f8 63%);
  background-size: 400% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}

.dashboard-skeleton__block--wide {
  height: 132px;
}

@keyframes shimmer {
  0% {
    background-position: 100% 0;
  }

  100% {
    background-position: 0 0;
  }
}
</style>
