<script setup lang="ts">
import { OField, OInput, OSelect, OSlider } from "@oruga-ui/oruga-next";

defineProps<{
  minDate?: string;
  maxDate?: string;
}>();

const retailer = defineModel<string>("retailer", { default: "" });
const startDate = defineModel<string>("startDate", { default: "" });
const endDate = defineModel<string>("endDate", { default: "" });
const timeGranularity = defineModel<string>("timeGranularity", { default: "Täglich" });
const spendingView = defineModel<string>("spendingView", { default: "Absolut" });
const topView = defineModel<string>("topView", { default: "Menge" });
const topLimit = defineModel<number>("topLimit", { default: 20 });
</script>

<template>
  <form class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm xl:grid-cols-3" @submit.prevent>
    <OField label="Händler">
      <OSelect v-model="retailer" expanded>
        <option value="">Alle</option>
        <option value="lidl">Lidl</option>
        <option value="rewe">REWE</option>
      </OSelect>
    </OField>

    <OField label="Startdatum">
      <OInput v-model="startDate" :min="minDate || undefined" :max="maxDate || undefined" type="date" expanded />
    </OField>

    <OField label="Enddatum">
      <OInput v-model="endDate" :min="minDate || undefined" :max="maxDate || undefined" type="date" expanded />
    </OField>

    <OField label="Zeitgranularität">
      <OSelect v-model="timeGranularity" expanded>
        <option>Täglich</option>
        <option>Monatlich</option>
        <option>Jährlich</option>
      </OSelect>
    </OField>

    <OField label="Ansicht">
      <OSelect v-model="spendingView" expanded>
        <option>Absolut</option>
        <option>Kumulativ</option>
      </OSelect>
    </OField>

    <OField label="Sortieren nach">
      <OSelect v-model="topView" expanded>
        <option>Menge</option>
        <option>Ausgaben</option>
      </OSelect>
    </OField>

    <OField class="xl:col-span-3" label="Anzahl anzeigen">
      <div class="space-y-2">
        <OSlider v-model="topLimit" :min="5" :max="50" :step="5" />
        <p class="text-sm text-slate-500">{{ topLimit }} Einträge</p>
      </div>
    </OField>
  </form>
</template>
