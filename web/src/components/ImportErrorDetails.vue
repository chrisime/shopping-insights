<script setup lang="ts">
import { ref } from "vue";
import { t } from "../utils/copy";

defineProps<{
  errorCode: number;
}>();

const showCode = ref(false);
</script>

<template>
  <p class="text-sm text-slate-500">
    <button
      data-testid="import-error-details-toggle"
      type="button"
      class="mr-2 underline decoration-slate-300 underline-offset-4"
      @click="showCode = !showCode"
    >
      {{ showCode ? t("import.errorDetails.hide") : t("import.errorDetails.show") }}
    </button>
    <span
      v-if="showCode"
      class="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-600"
    >
      {{ t("import.errorDetails.code", { code: errorCode }) }}
    </span>
  </p>
</template>
