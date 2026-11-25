import { fileURLToPath } from "node:url";
import { defineConfig } from "@playwright/test";

const port = 44191;
const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.e2e.ts",
  use: { baseURL, browserName: "chromium" },
  webServer: {
    command: `uv run --locked uvicorn api.main:app --host 127.0.0.1 --port ${port}`,
    cwd: fileURLToPath(new URL("../", import.meta.url)),
    url: baseURL,
    reuseExistingServer: false,
  },
});
