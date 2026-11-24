<script setup lang="ts">
import { OField, OSelect } from "@oruga-ui/oruga-next";
import { computed, ref, watch } from "vue";

import ImportJobProgress from "./ImportJobProgress.vue";
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

const authMode = ref<"mfa-login" | "cookies-file" | "user-login">("mfa-login");
const browser = ref<(typeof BROWSER_OPTIONS)[number]["value"]>("firefox");
const cookiesFile = ref("lidl_cookies.json");
const customerId = ref("");
const showCustomerId = ref(false);
const loginEmail = ref("");
const loginPassword = ref("");

function applyRetailerDefaults(retailer: ImportRetailer) {
  const defaultFiles: Record<ImportRetailer, string> = {
    lidl: "lidl_cookies.json",
    rewe: "rewe_cookies.json",
    dm: "dm_cookies.json",
    rossmann: "rossmann_cookies.json",
  };

  browser.value = "firefox";
  cookiesFile.value = defaultFiles[retailer];
  authMode.value = retailer === "rossmann" ? "user-login" : "mfa-login";
  customerId.value = "";
  showCustomerId.value = false;
  loginEmail.value = "";
  loginPassword.value = "";
}

watch(
  () => props.retailer,
  (retailer) => {
    applyRetailerDefaults(retailer);
  },
  { immediate: true },
);

watch(authMode, () => {
  loginPassword.value = "";
});

const canStart = computed(
  () =>
    !props.running &&
    (authMode.value !== "user-login" ||
      Boolean(loginEmail.value.trim() && loginPassword.value.trim())),
);

function submitImport() {
  if (!canStart.value) return;

  const payload: ImportStartRequest = { retailer: props.retailer };
  if (authMode.value === "user-login") {
    payload.user_login = {
      email: loginEmail.value.trim(),
      password: loginPassword.value,
    };
    loginPassword.value = "";
  } else if (authMode.value === "mfa-login") {
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
    <form data-testid="import-form" class="grid gap-4" @submit.prevent="submitImport">
      <div class="grid gap-4 sm:grid-cols-2">
        <OField :label="t('import.forRetailer')">
          <OSelect
            :model-value="retailer"
            expanded
            @update:model-value="emit('update:retailer', $event as ImportRetailer)"
          >
            <option data-testid="import-option" value="lidl">{{ t("retailer.lidl") }}</option>
            <option data-testid="import-option" value="rewe">{{ t("retailer.rewe") }}</option>
            <option data-testid="import-option" value="dm">{{ t("retailer.dm") }}</option>
            <option data-testid="import-option" value="rossmann">
              {{ t("retailer.rossmann") }}
            </option>
          </OSelect>
        </OField>

        <div class="grid gap-4 sm:grid-cols-2">
          <OField :label="t('import.authentication')">
            <OSelect v-model="authMode" expanded>
              <option data-testid="import-option" v-if="retailer === 'rossmann'" value="user-login">
                {{ t("import.rossmannAccount") }}
              </option>
              <option data-testid="import-option" v-else value="mfa-login">
                {{ t("import.browserProfile") }}
              </option>
              <option data-testid="import-option" value="cookies-file">
                {{ t("import.cookieFile") }}
              </option>
            </OSelect>
          </OField>

          <OField v-if="authMode === 'mfa-login'" :label="t('import.browser')">
            <OSelect v-model="browser" expanded>
              <option
                data-testid="import-option"
                v-for="option in BROWSER_OPTIONS"
                :key="option.value"
                :value="option.value"
              >
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

      <div v-if="authMode === 'user-login'" class="grid gap-4 sm:grid-cols-2">
        <OField :label="t('import.rossmannEmail')" label-for="rossmann-import-email">
          <input
            data-testid="import-email"
            id="rossmann-import-email"
            v-model="loginEmail"
            autocomplete="username"
            type="email"
            required
            class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
          />
        </OField>
        <OField :label="t('import.rossmannPassword')" label-for="rossmann-import-password">
          <input
            data-testid="import-password"
            id="rossmann-import-password"
            v-model="loginPassword"
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
          data-testid="import-customer-id-toggle"
          @click="showCustomerId = !showCustomerId"
        >
          {{ showCustomerId ? t("import.customerId.hide") : t("import.customerId.show") }}
        </button>
        <OField v-if="showCustomerId" :label="t('import.customerId.label')">
          <input
            data-testid="import-customer-id"
            v-model="customerId"
            class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
            type="text"
            :placeholder="t('common.optional')"
          />
        </OField>
      </div>

      <button
        data-testid="import-submit"
        type="submit"
        class="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="!canStart"
      >
        {{ running ? t("import.running") : t("import.start") }}
      </button>
    </form>

    <ImportJobProgress
      :progress="progress"
      :message="message"
      :error="error"
      :technical-error="technicalError"
    />
  </section>
</template>
