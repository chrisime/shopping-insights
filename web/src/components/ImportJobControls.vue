<script setup lang="ts">
import { OField, OSelect } from "@oruga-ui/oruga-next";
import { computed, ref, watch } from "vue";

import ImportErrorDetails from "./ImportErrorDetails.vue";
import type {
  ImportProgressState,
  ImportRetailer,
  ImportStartRequest,
  ImportTechnicalError,
} from "../types/imports";
import { t } from "../utils/copy";

const BROWSER_OPTIONS = [
  { value: "firefox", labelKey: "import.browser.firefox" },
  { value: "librewolf", labelKey: "import.browser.librewolf" },
  { value: "chrome", labelKey: "import.browser.chrome" },
  { value: "chromium", labelKey: "import.browser.chromium" },
] as const;

const props = defineProps<{
  retailer: ImportRetailer;
  running: boolean;
  progress: ImportProgressState;
  message: string | null;
  error: string | null;
  technicalError?: ImportTechnicalError | null;
}>();

const emit = defineEmits<{
  (event: "update:retailer", value: ImportRetailer): void;
  (event: "start-import", payload: ImportStartRequest): void;
}>();

const authMode = ref<"browser" | "cookies-file" | "rossmann-login">("browser");
const browser = ref<(typeof BROWSER_OPTIONS)[number]["value"]>("firefox");
const cookiesFile = ref("lidl_cookies.json");
const customerId = ref("");
const showCustomerId = ref(false);
const rossmannEmail = ref("");
const rossmannPassword = ref("");

function applyRetailerDefaults(retailer: ImportRetailer) {
  browser.value = "firefox";
  const defaultFiles: Record<ImportRetailer, string> = {
    lidl: "lidl_cookies.json",
    rewe: "rewe_cookies.json",
    dm: "dm_cookies.json",
    rossmann: "rossmann_cookies.json",
  };
  cookiesFile.value = defaultFiles[retailer] ?? "lidl_cookies.json";
  authMode.value = retailer === "rossmann" ? "rossmann-login" : "browser";
  customerId.value = "";
  showCustomerId.value = false;
  rossmannEmail.value = "";
  rossmannPassword.value = "";
}

watch(
  () => props.retailer,
  (retailer) => {
    applyRetailerDefaults(retailer);
  },
  { immediate: true },
);

watch(authMode, () => {
  rossmannPassword.value = "";
});

const canStart = computed(
  () =>
    !props.running &&
    (authMode.value !== "rossmann-login" ||
      Boolean(rossmannEmail.value.trim() && rossmannPassword.value)),
);

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

function submitImport() {
  if (!canStart.value) return;

  const payload: ImportStartRequest = { retailer: props.retailer };
  if (authMode.value === "rossmann-login") {
    payload.rossmann_login = {
      email: rossmannEmail.value.trim(),
      password: rossmannPassword.value,
    };
    rossmannPassword.value = "";
  } else if (authMode.value === "browser") {
    payload.browser = browser.value;
  } else {
    payload.cookies_file = cookiesFile.value;
  }
  if (props.retailer === "rewe") {
    payload.customer_id = customerId.value || null;
  }
  emit("start-import", payload);
}
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
    <form class="grid gap-4" @submit.prevent="submitImport">
      <div class="grid gap-4 sm:grid-cols-2">
        <OField :label="t('import.forRetailer')">
          <OSelect
            :model-value="retailer"
            expanded
            @update:model-value="emit('update:retailer', $event as ImportRetailer)"
          >
            <option value="lidl">{{ t("retailer.lidl") }}</option>
            <option value="rewe">{{ t("retailer.rewe") }}</option>
            <option value="dm">{{ t("retailer.dm") }}</option>
            <option value="rossmann">{{ t("retailer.rossmann") }}</option>
          </OSelect>
        </OField>

        <div class="grid gap-4 sm:grid-cols-2">
          <OField :label="t('import.authentication')">
            <OSelect v-model="authMode" expanded>
              <option v-if="retailer === 'rossmann'" value="rossmann-login">
                {{ t("import.rossmannAccount") }}
              </option>
              <option v-else value="browser">{{ t("import.browserProfile") }}</option>
              <option value="cookies-file">{{ t("import.cookieFile") }}</option>
            </OSelect>
          </OField>

          <OField v-if="authMode === 'browser'" :label="t('import.browser')">
            <OSelect v-model="browser" expanded>
              <option v-for="option in BROWSER_OPTIONS" :key="option.value" :value="option.value">
                {{ t(option.labelKey) }}
              </option>
            </OSelect>
          </OField>

          <OField v-if="authMode === 'cookies-file'" :label="t('import.cookieFile')">
            <input
              v-model="cookiesFile"
              class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
              type="text"
            />
          </OField>
        </div>
      </div>

      <div v-if="authMode === 'rossmann-login'" class="grid gap-4 sm:grid-cols-2">
        <OField :label="t('import.rossmannEmail')" label-for="rossmann-import-email">
          <input
            id="rossmann-import-email"
            v-model="rossmannEmail"
            autocomplete="username"
            type="email"
            required
            class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
          />
        </OField>
        <OField :label="t('import.rossmannPassword')" label-for="rossmann-import-password">
          <input
            id="rossmann-import-password"
            v-model="rossmannPassword"
            autocomplete="current-password"
            type="password"
            required
            class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
          />
        </OField>
      </div>

      <div v-if="retailer === 'rewe'" class="space-y-2">
        <button
          type="button"
          class="text-sm font-medium text-slate-600 underline decoration-slate-300 underline-offset-4"
          @click="showCustomerId = !showCustomerId"
        >
          {{ showCustomerId ? t("import.customerId.hide") : t("import.customerId.show") }}
        </button>
        <OField v-if="showCustomerId" :label="t('import.customerId.label')">
          <input
            v-model="customerId"
            class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
            type="text"
            :placeholder="t('common.optional')"
          />
        </OField>
      </div>

      <button
        type="submit"
        class="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="!canStart"
      >
        {{ running ? t("import.running") : t("import.start") }}
      </button>
    </form>

    <div class="mt-4 space-y-2">
      <div class="h-2 overflow-hidden rounded-full bg-slate-100">
        <div
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
  </section>
</template>
