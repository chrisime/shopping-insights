import { createApp, defineComponent, h } from "vue";

const App = defineComponent({
  name: "ShoppingAnalyzerApp",
  setup() {
    return () =>
      h("main", { class: "app-shell" }, [
        h("h1", "Shopping Analyzer Dashboard"),
        h("p", "Vue dashboard scaffold ready."),
      ]);
  },
});

createApp(App).mount("#app");
