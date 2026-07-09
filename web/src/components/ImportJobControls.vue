<script setup lang="ts">
import { OField, OSelect } from "@oruga-ui/oruga-next";
import { computed, ref, watch } from "vue";

import ImportErrorDetails from "./ImportErrorDetails.vue";
import type { ImportProgressState, ImportRetailer, ImportStartRequest } from "../types/imports";

const BROWSER_OPTIONS = [
  { value: "firefox", label: "Firefox" },
  { value: "librewolf", label: "LibreWolf" },
  { value: "chrome", label: "Chrome" },
  { value: "chromium", label: "Chromium" },
] as const;

const props = defineProps<{
  retailer: ImportRetailer;
  running: boolean;
  progress: ImportProgressState;
  message: string | null;
  error: string | null;
  technicalError?: { error_code: number; detail: string } | null;
}>();

const emit = defineEmits<{
  (event: "update:retailer", value: ImportRetailer): void;
  (event: "start-import", payload: ImportStartRequest): void;
}>();

const authMode = ref<"browser" | "cookies-file">("browser");
const browser = ref<(typeof BROWSER_OPTIONS)[number]["value"]>("firefox");
const cookiesFile = ref("lidl_cookies.json");
const customerId = ref("");
const showCustomerId = ref(false);

function applyRetailerDefaults(retailer: ImportRetailer) {
  authMode.value = "cookies-file";
  browser.value = "firefox";
  cookiesFile.value = retailer === "lidl" ? "lidl_cookies.json" : "rewe_cookies.json";
  authMode.value = "browser";
  customerId.value = "";
  showCustomerId.value = false;
}

watch(
  () => props.retailer,
  (retailer) => {
    applyRetailerDefaults(retailer);
  },
  { immediate: true },
);

const startPayload = computed(() =>
  authMode.value === "browser"
    ? props.retailer === "rewe"
      ? { retailer: props.retailer, browser: browser.value, customer_id: customerId.value || null }
      : { retailer: props.retailer, browser: browser.value }
    : props.retailer === "rewe"
      ? { retailer: props.retailer, cookies_file: cookiesFile.value, customer_id: customerId.value || null }
      : { retailer: props.retailer, cookies_file: cookiesFile.value },
);
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

      <OField label="Authentifizierung">
        <OSelect v-model="authMode" expanded>
          <option value="browser">Browser-Profil</option>
          <option value="cookies-file">Cookie-Datei</option>
        </OSelect>
      </OField>

      <OField v-if="authMode === 'browser'" label="Browser">
        <OSelect v-model="browser" expanded>
          <option v-for="option in BROWSER_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option>
        </OSelect>
      </OField>

      <div v-if="retailer === 'rewe'" class="space-y-2">
        <button type="button" class="text-sm font-medium text-slate-600 underline decoration-slate-300 underline-offset-4" @click="showCustomerId = !showCustomerId">
          {{ showCustomerId ? "customerId verbergen" : "customerId optional eingeben" }}
        </button>
        <OField v-if="showCustomerId" label="REWE customerId">
          <input v-model="customerId" class="rounded-xl border border-slate-300 px-3 py-2 text-sm" type="text" placeholder="optional" />
        </OField>
      </div>

      <OField v-if="authMode === 'cookies-file'" label="Cookie-Datei">
        <input v-model="cookiesFile" class="rounded-xl border border-slate-300 px-3 py-2 text-sm" type="text" />
      </OField>

      <button
        type="button"
        class="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="running"
        @click="emit('start-import', startPayload)"
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

      <div class="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <article class="grid gap-1 rounded-2xl border border-slate-200 bg-slate-50/80 p-3 shadow-sm ring-1 ring-slate-100/70">
          <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Neu</span>
          <strong class="text-xl font-semibold tracking-tight text-slate-900">{{ progress.added }}</strong>
        </article>
        <article class="grid gap-1 rounded-2xl border border-slate-200 bg-slate-50/80 p-3 shadow-sm ring-1 ring-slate-100/70">
          <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Übersprungen</span>
          <strong class="text-xl font-semibold tracking-tight text-slate-900">{{ progress.skipped }}</strong>
        </article>
        <article class="grid gap-1 rounded-2xl border border-slate-200 bg-slate-50/80 p-3 shadow-sm ring-1 ring-slate-100/70">
          <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Fehler</span>
          <strong class="text-xl font-semibold tracking-tight text-slate-900">{{ progress.errors }}</strong>
        </article>
        <article class="grid gap-1 rounded-2xl border border-slate-200 bg-slate-50/80 p-3 shadow-sm ring-1 ring-slate-100/70">
          <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Artikel</span>
          <strong class="text-xl font-semibold tracking-tight text-slate-900">{{ progress.items }}</strong>
        </article>
      </div>
      <p class="text-sm font-medium text-slate-700">
        {{ progress.current }}/{{ progress.total }} · {{ progress.current_receipt }}
      </p>
      <p v-if="message" class="text-sm text-slate-500">{{ message }}</p>
      <p v-if="error" class="text-sm text-rose-600">{{ error }}</p>
      <ImportErrorDetails v-if="technicalError" :error-code="technicalError.error_code" />
    </div>
  </section>
</template>
