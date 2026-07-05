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
