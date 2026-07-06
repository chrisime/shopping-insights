<script setup lang="ts">
import { OField, OSelect } from "@oruga-ui/oruga-next";

import type { ImportProgressState, ImportRetailer } from "../types/imports";

defineProps<{
  retailer: ImportRetailer;
  running: boolean;
  progress: ImportProgressState;
  message: string | null;
  error: string | null;
}>();

const emit = defineEmits<{
  (event: "update:retailer", value: ImportRetailer): void;
  (event: "start-import"): void;
}>();
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="grid gap-4 lg:grid-cols-[minmax(0,18rem)_auto] lg:items-end">
      <OField label="Importieren für">
        <OSelect :model-value="retailer" expanded @update:model-value="emit('update:retailer', $event as ImportRetailer)">
          <option value="lidl">Lidl</option>
          <option value="rewe">REWE</option>
        </OSelect>
      </OField>

      <button
        type="button"
        class="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="running"
        @click="emit('start-import')"
      >
        {{ running ? "Import läuft..." : "Import" }}
      </button>
    </div>

    <div class="mt-4 space-y-2">
      <div class="h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          class="h-full rounded-full bg-emerald-500 transition-all"
          :style="{ width: `${progress.total > 0 ? Math.min(100, Math.round((progress.current / progress.total) * 100)) : 0}%` }"
        />
      </div>

      <p class="text-sm font-medium text-slate-700">
        {{ progress.current }}/{{ progress.total }} · {{ progress.current_receipt }}
      </p>
      <p class="text-sm text-slate-500">
        Neu: {{ progress.added }} · Übersprungen: {{ progress.skipped }} · Fehler: {{ progress.errors }} · Artikel: {{ progress.items }}
      </p>
      <p v-if="message" class="text-sm text-slate-500">{{ message }}</p>
      <p v-if="error" class="text-sm text-rose-600">{{ error }}</p>
    </div>
  </section>
</template>
