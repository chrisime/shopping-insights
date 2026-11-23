<script setup lang="ts">
import { t } from "../utils/copy";

export type SidebarTab = "import" | "ausgaben" | "einkauf" | "artikel";

const activeTab = defineModel<SidebarTab>("activeTab", { required: true });
const collapsed = defineModel<boolean>("collapsed", { required: true });

const tabs: { key: SidebarTab; icon: string; label: string }[] = [
  { key: "import", icon: "📥", label: t("tabs.import") },
  { key: "ausgaben", icon: "💰", label: t("tabs.spending") },
  { key: "einkauf", icon: "📊", label: t("tabs.shopping") },
  { key: "artikel", icon: "🛒", label: t("tabs.items") },
];
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
      @click="collapsed = !collapsed"
    >
      <span class="sr-only">{{ collapsed ? t("sidebar.expand") : t("sidebar.collapse") }}</span>
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
        @click="activeTab = tab.key"
      >
        <span class="text-lg">{{ tab.icon }}</span>
        <span v-if="!collapsed" class="truncate">{{ tab.label }}</span>
      </button>
    </nav>
  </aside>
</template>
