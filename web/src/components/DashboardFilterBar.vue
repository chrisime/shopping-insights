<script setup lang="ts">
import { OField, OInput, OSelect } from "@oruga-ui/oruga-next";

const search = defineModel<string>("search", { default: "" });
const topView = defineModel<string>("topView", { default: "Menge" });
</script>

<template>
  <form class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm" @submit.prevent>
    <h2 class="text-lg font-semibold tracking-tight text-slate-900">Artikel Filter</h2>
    <div class="grid gap-4 sm:grid-cols-2">
      <OField label="Artikelsuche">
        <OInput v-model="search" placeholder="Mind. 3 Zeichen" expanded />
      </OField>

      <OField label="Sortieren nach">
        <OSelect v-model="topView" expanded>
          <option>Menge</option>
          <option>Ausgaben</option>
        </OSelect>
      </OField>
    </div>
  </form>
</template>
