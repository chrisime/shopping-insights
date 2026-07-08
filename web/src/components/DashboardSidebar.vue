<script setup lang="ts">
import { computed } from "vue";

export type SidebarTab = "import" | "ausgaben" | "einkauf" | "artikel";

const props = defineProps<{
  activeTab: SidebarTab;
  collapsed: boolean;
}>();

const emit = defineEmits<{
  (e: "update:active-tab", value: SidebarTab): void;
  (e: "update:collapsed", value: boolean): void;
}>();

const tabs: { key: SidebarTab; icon: string; label: string }[] = [
  { key: "import", icon: "📥", label: "Import" },
  { key: "ausgaben", icon: "💰", label: "Ausgaben" },
  { key: "einkauf", icon: "📊", label: "Einkaufsverhalten" },
  { key: "artikel", icon: "🛒", label: "Artikel" },
];

function select(key: SidebarTab) {
  emit("update:active-tab", key);
}

function toggle() {
  emit("update:collapsed", !props.collapsed);
}
</script>

<template>
  <aside
    :class="[
      'flex shrink-0 flex-col border-r border-slate-200 bg-white transition-all duration-200',
      collapsed ? 'w-16' : 'w-48',
    ]"
  >
    <button
      type="button"
      class="flex h-14 items-center justify-center border-b border-slate-200 text-lg text-slate-500 hover:text-slate-700"
      @click="toggle"
    >
      {{ collapsed ? "☰" : "✕" }}
    </button>

    <nav class="flex flex-col gap-1 px-2 py-4">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        :class="[
          'flex items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium transition',
          activeTab === tab.key
            ? 'bg-indigo-50 text-indigo-700'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
        ]"
        @click="select(tab.key)"
      >
        <span class="text-lg">{{ tab.icon }}</span>
        <span v-if="!collapsed" class="truncate">{{ tab.label }}</span>
      </button>
    </nav>
  </aside>
</template>
