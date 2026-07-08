<script setup lang="ts">
import { ref, watch } from "vue";
import { fetchReceiptsByItem } from "../api/dashboard";

const props = defineProps<{
  articleName: string;
  retailer?: string;
  visible: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

const loading = ref(false);
const receipts = ref<Array<Record<string, unknown>>>([]);
const currentIndex = ref(0);
const requestTicket = ref(0);

watch(
  () => props.visible,
  async (show) => {
    if (!show) return;
    loading.value = true;
    receipts.value = [];
    currentIndex.value = 0;
    const ticket = ++requestTicket.value;
    try {
      const result = await fetchReceiptsByItem(props.articleName, props.retailer);
      if (ticket === requestTicket.value) receipts.value = result;
    } finally {
      if (ticket === requestTicket.value) loading.value = false;
    }
  },
);

const current = ref<Record<string, unknown>>({});
watch(
  [receipts, currentIndex],
  () => {
    current.value = receipts.value[currentIndex.value] ?? {};
  },
  { immediate: true },
);

function prev() {
  if (currentIndex.value > 0) currentIndex.value--;
}

function next() {
  if (currentIndex.value < receipts.value.length - 1) currentIndex.value++;
}

function text(value: unknown) {
  return value == null ? "-" : String(value);
}

function currency(value: unknown) {
  const numeric = typeof value === "number" ? value : Number(value ?? 0);
  return Number.isFinite(numeric) ? `\u20AC${numeric.toFixed(2)}` : "-";
}

function isMatched(item: Record<string, unknown>): boolean {
  return item.matched === true;
}

function retailerLabel(value: unknown): string {
  if (value === "lidl") return "Lidl";
  if (value === "rewe") return "REWE";
  return text(value);
}

function addressText(addr: unknown): string {
  if (!addr || typeof addr !== "object") return "";
  const a = addr as Record<string, unknown>;
  const parts = [
    a.street && a.street_no ? `${a.street} ${a.street_no}` : a.street || "",
    a.zip && a.city ? `${a.zip} ${a.city}` : a.city || a.zip || "",
  ].filter(Boolean);
  return parts.join(", ");
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      @click.self="emit('close')"
    >
      <div class="flex max-h-[85vh] w-full max-w-2xl flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl">
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <h2 class="text-lg font-semibold tracking-tight text-slate-900">
            {{ articleName }} — {{ retailerLabel(current.retailer) }} Kassenzettel
          </h2>
          <button
            type="button"
            class="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
            @click="emit('close')"
          >
            <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="flex items-center justify-center py-16 text-sm text-slate-500">
          Lade Kassenzettel...
        </div>

        <!-- No receipts -->
        <div v-else-if="receipts.length === 0" class="flex items-center justify-center py-16 text-sm text-slate-500">
          Keine Kassenzettel gefunden.
        </div>

        <!-- Receipt content -->
        <template v-else>
          <!-- Navigation -->
          <div v-if="receipts.length > 1" class="flex items-center justify-between border-b border-slate-100 px-5 py-2.5">
            <button
              type="button"
              :disabled="currentIndex <= 0"
              class="rounded-lg border border-slate-300 bg-white px-3 py-1 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              @click="prev"
            >
              Zurück
            </button>
            <span class="text-sm text-slate-500">
              {{ currentIndex + 1 }} von {{ receipts.length }}
            </span>
            <button
              type="button"
              :disabled="currentIndex >= receipts.length - 1"
              class="rounded-lg border border-slate-300 bg-white px-3 py-1 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              @click="next"
            >
              Weiter
            </button>
          </div>

          <!-- Receipt detail -->
          <div class="overflow-y-auto px-5 py-4">
            <div class="mb-4 grid grid-cols-4 gap-3 text-sm">
              <div>
                <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Händler</p>
                <p class="mt-0.5 font-bold uppercase text-slate-900">{{ retailerLabel(current.retailer) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Markt</p>
                <p class="mt-0.5 font-medium text-slate-900">{{ text(current.store) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Adresse</p>
                <p class="mt-0.5 text-xs text-slate-500">{{ addressText(current.address) }}</p>
              </div>
              <div class="text-right">
                <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Datum</p>
                <p class="mt-0.5 font-medium text-slate-900">{{ text(current.purchase_date) }}</p>
              </div>
            </div>

            <div class="border-t border-slate-200 pt-3">
              <h3 class="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Artikel</h3>
              <div class="divide-y divide-slate-100">
                <div
                  v-for="(item, ii) in (current.items as Array<Record<string, unknown>> || [])"
                  :key="ii"
                  class="flex items-center justify-between gap-3 px-3 py-2 text-sm"
                  :class="isMatched(item) ? '-mx-3 rounded-xl bg-amber-50 px-3 ring-1 ring-amber-300' : ''"
                >
                  <div class="flex items-center gap-2">
                    <span v-if="isMatched(item)" class="h-2 w-2 rounded-full bg-amber-400" />
                    <span :class="isMatched(item) ? 'font-semibold text-amber-900' : 'text-slate-700'">
                      {{ text(item.name) }}
                    </span>
                  </div>
                  <span class="shrink-0 text-slate-600">
                    {{ Number(item.quantity)?.toLocaleString("de-DE") }} {{ text(item.unit) }} × {{ currency(item.price) }}
                  </span>
                </div>
              </div>
            </div>

            <div class="mt-4 border-t border-slate-200 pt-3 text-right">
              <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Gesamt</span>
              <p class="text-xl font-semibold text-slate-900">{{ currency(current.total_price) }}</p>
            </div>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>
