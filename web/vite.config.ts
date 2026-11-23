import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";
import { defineConfig, lazyPlugins } from "vite-plus";

export default defineConfig({
  fmt: {},
  lint: {
    jsPlugins: [{ name: "vite-plus", specifier: "vite-plus/oxlint-plugin" }],
    rules: { "vite-plus/prefer-vite-plus-imports": "error" },
    options: { typeAware: true, typeCheck: true },
  },
  plugins: lazyPlugins(() => [vue(), tailwindcss()]),
  run: {
    tasks: {
      typecheck: {
        command: "vue-tsc --noEmit",
      },
    },
  },
  test: {
    environment: "node",
    setupFiles: ["./src/test/setup.ts"],
  },
});
