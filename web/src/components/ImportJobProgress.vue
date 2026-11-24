<script setup lang="ts">
import { computed } from "vue";

import ImportErrorDetails from "./ImportErrorDetails.vue";
import type { ImportProgressState, ImportTechnicalError } from "../types/imports";
import { t } from "../utils/copy";

const props = defineProps<{
  progress: ImportProgressState;
  message: string | null;
  error: string | null;
  technicalError?: ImportTechnicalError | null;
}>();

const progressPercent = computed(() =>
  props.progress.total > 0
    ? Math.min(100, Math.round((props.progress.current / props.progress.total) * 100))
    : 0,
);

const progressStats = computed(() => [
  { label: t("import.stat.added"), value: props.progress.added },
  { label: t("import.stat.skipped"), value: props.progress.skipped },
  { label: t("import.stat.errors"), value: props.progress.errors },
  { label: t("import.stat.items"), value: props.progress.items },
]);
</script>

<template>
  <div class="mt-4 space-y-2">
    <div data-testid="import-progress-track" class="h-2 overflow-hidden rounded-full bg-slate-100">
      <div
        data-testid="import-progress-fill"
        class="h-full rounded-full bg-emerald-500 transition-all"
        :style="{ width: `${progressPercent}%` }"
      />
    </div>

    <div class="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
      <article
        v-for="stat in progressStats"
        :key="stat.label"
        class="grid gap-1 rounded-2xl border border-slate-200 bg-slate-50/80 p-3 shadow-sm ring-1 ring-slate-100/70"
      >
        <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">{{
          stat.label
        }}</span>
        <strong class="text-xl font-semibold tracking-tight text-slate-900">{{
          stat.value
        }}</strong>
      </article>
    </div>
    <p class="text-sm font-medium text-slate-700">
      {{ progress.current }}/{{ progress.total }} · {{ progress.current_receipt }}
    </p>
    <p v-if="message" class="text-sm text-slate-500">{{ message }}</p>
    <p v-if="error" class="text-sm text-rose-600">{{ error }}</p>
    <ImportErrorDetails v-if="technicalError" :error-code="technicalError.error_code" />
  </div>
</template>
