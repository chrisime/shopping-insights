<script setup lang="ts">
import { OField, OInput, OSelect } from "@oruga-ui/oruga-next";

const search = defineModel<string>("search", { default: "" });
const topLimit = defineModel<number>("topLimit", { default: 20 });
</script>

<template>
  <form class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm xl:grid-cols-2" @submit.prevent>
    <OField label="Artikelsuche">
      <OInput v-model="search" placeholder="Mind. 3 Zeichen" expanded />
    </OField>

    <OField label="Einträge pro Seite">
      <OSelect v-model="topLimit" expanded>
        <option :value="10">10</option>
        <option :value="20">20</option>
        <option :value="50">50</option>
      </OSelect>
    </OField>
  </form>
</template>
