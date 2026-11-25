import { constants } from "node:zlib";
import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";
import { defineConfig, lazyPlugins } from "vite-plus";
import { compression, defineAlgorithm } from "vite-plugin-compression2";

export default defineConfig({
  fmt: {},
  lint: {
    jsPlugins: [{ name: "vite-plus", specifier: "vite-plus/oxlint-plugin" }],
    rules: { "vite-plus/prefer-vite-plus-imports": "error" },
    options: { typeAware: true, typeCheck: true },
  },
  plugins: lazyPlugins(() => [
    vue(),
    tailwindcss(),
    compression({
      include: /^assets\/.*\.(?:css|js)$/,
      algorithms: [
        defineAlgorithm("brotliCompress", { params: { [constants.BROTLI_PARAM_QUALITY]: 11 } }),
        defineAlgorithm("gzip", { level: 9 }),
      ],
      skipIfLargerOrEqual: false,
    }),
  ]),
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            {
              name: "echarts-vendor",
              // Keep shared Vue modules on the startup path.
              includeDependenciesRecursively: false,
              test: /[\\/]node_modules[\\/](?:echarts|zrender|vue-echarts|tslib)[\\/]/,
            },
          ],
        },
      },
    },
  },
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
