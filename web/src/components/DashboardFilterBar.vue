<script setup lang="ts">
const retailer = defineModel<string>("retailer", { default: "" });
const startDate = defineModel<string>("startDate", { default: "" });
const endDate = defineModel<string>("endDate", { default: "" });
const timeGranularity = defineModel<string>("timeGranularity", { default: "Täglich" });
const spendingView = defineModel<string>("spendingView", { default: "Absolut" });
const topView = defineModel<string>("topView", { default: "Menge" });
const topLimit = defineModel<number>("topLimit", { default: 20 });
</script>

<template>
  <form class="filter-bar" @submit.prevent>
    <label>
      Händler
      <select v-model="retailer">
        <option value="">Alle</option>
        <option value="lidl">Lidl</option>
        <option value="rewe">REWE</option>
      </select>
    </label>

    <label>
      Startdatum
      <input v-model="startDate" type="date" />
    </label>

    <label>
      Enddatum
      <input v-model="endDate" type="date" />
    </label>

    <label>
      Zeitgranularität
      <select v-model="timeGranularity">
        <option>Täglich</option>
        <option>Monatlich</option>
        <option>Jährlich</option>
      </select>
    </label>

    <label>
      Ansicht
      <select v-model="spendingView">
        <option>Absolut</option>
        <option>Kumulativ</option>
      </select>
    </label>

    <label>
      Sortieren nach
      <select v-model="topView">
        <option>Menge</option>
        <option>Ausgaben</option>
      </select>
    </label>

    <label>
      Anzahl anzeigen
      <input v-model.number="topLimit" type="range" min="5" max="50" step="5" />
      <span>{{ topLimit }}</span>
    </label>
  </form>
</template>

<style scoped>
.filter-bar {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  padding: 1rem;
  border: 1px solid #d8dee6;
  border-radius: 14px;
  background: #fff;
}

label {
  display: grid;
  gap: 0.35rem;
  font-size: 0.92rem;
}

select,
input[type="date"],
input[type="range"] {
  width: 100%;
}

span {
  font-variant-numeric: tabular-nums;
}
</style>
