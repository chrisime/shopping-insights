<script setup lang="ts">
import { ref } from "vue";

defineProps<{
  errorCode: number;
}>();

const showCode = ref(false);
</script>

<template>
  <p class="text-sm text-slate-500">
    <button type="button" class="mr-2 underline decoration-slate-300 underline-offset-4" @click="showCode = !showCode">
      {{ showCode ? "Debug-Infos verbergen" : "Debug-Infos anzeigen" }}
    </button>
    <span v-if="showCode" class="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-600">
      Code {{ errorCode }}
    </span>
  </p>
</template>
