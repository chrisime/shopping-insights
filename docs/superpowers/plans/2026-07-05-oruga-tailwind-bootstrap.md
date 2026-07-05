# Oruga and Tailwind Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Register Oruga in the Vue bootstrap, load Tailwind base styles, and ensure Vite compiles the Tailwind entry without changing dashboard behavior.

**Architecture:** Keep the existing Vue app structure intact. The app entrypoint will own plugin registration and global stylesheet imports; the stylesheet will own Tailwind and minimal base defaults; Vite config will own the Tailwind plugin so builds and tests see the same CSS pipeline.

**Tech Stack:** Vue 3, Oruga Next, Tailwind CSS, Vite, Vitest.

## Global Constraints

- Keep the existing payload and dashboard behavior unchanged.
- The work should be minimal: register Oruga, load Tailwind base styles, and update the Vite build so Tailwind compiles.
- Do not push anything to GitHub.
- Use TDD and keep the implementation small and readable.

---

### Task 1: Bootstrap Oruga and Tailwind

**Files:**
- Modify: `web/package.json`
- Modify: `web/package-lock.json`
- Modify: `web/vite.config.ts`
- Modify: `web/src/main.ts`
- Create: `web/src/styles.css`
- Create: `web/src/__tests__/main.spec.ts`

**Interfaces:**
- Consumes: the Vue app bootstrap in `web/src/main.ts`
- Produces: Oruga plugin registration, Tailwind base styles, and a global stylesheet entrypoint for later dashboard components

- [ ] **Step 1: Write the failing test**

```ts
import { describe, expect, it, vi } from "vitest";

const mountMock = vi.fn();
const useMock = vi.fn(() => ({ mount: mountMock }));

vi.mock("vue", () => ({
  createApp: vi.fn(() => ({ use: useMock })),
}));

vi.mock("../App.vue", () => ({ default: { name: "App" } }));
vi.mock("@oruga-ui/oruga-next", () => ({ default: { name: "OrugaPlugin" } }));

describe("main bootstrap", () => {
  it("registers Oruga and mounts the app", async () => {
    await import("../main");

    expect(useMock).toHaveBeenCalledTimes(1);
    expect(mountMock).toHaveBeenCalledWith("#app");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd web && npm test -- --run src/__tests__/main.spec.ts`

Expected: FAIL because Oruga is not installed/registered yet and `main.ts` does not use the plugin or Tailwind stylesheet yet.

- [ ] **Step 3: Write the minimal implementation**

Install the UI dependencies:

```bash
npm install @oruga-ui/oruga-next
npm install -D tailwindcss @tailwindcss/vite
```

Update `web/src/main.ts`:

```ts
import { createApp } from "vue";
import Oruga from "@oruga-ui/oruga-next";

import App from "./App.vue";
import "@oruga-ui/oruga-next/dist/oruga.css";
import "./styles.css";

createApp(App).use(Oruga).mount("#app");
```

Create `web/src/styles.css`:

```css
@import "tailwindcss";

html,
body,
#app {
  min-height: 100%;
}

body {
  margin: 0;
  background: #f8fafc;
  color: #0f172a;
  font-family: ui-sans-serif, system-ui, sans-serif;
}
```

Update `web/vite.config.ts`:

```ts
import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  test: {
    environment: "node",
  },
});
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd web && npm test -- --run src/__tests__/main.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/package.json web/package-lock.json web/vite.config.ts web/src/main.ts web/src/styles.css web/src/__tests__/main.spec.ts docs/superpowers/plans/2026-07-05-oruga-tailwind-bootstrap.md
git commit -m "feat: bootstrap oruga and tailwind"
```
