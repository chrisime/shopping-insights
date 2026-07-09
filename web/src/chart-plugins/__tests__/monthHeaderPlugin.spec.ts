import { describe, expect, it } from "vitest";
import { monthHeaderPlugin } from "../monthHeaderPlugin";

describe("monthHeaderPlugin", () => {
  it("exports a Chart.js plugin with id monthHeader", () => {
    expect(monthHeaderPlugin).toBeDefined();
    expect(monthHeaderPlugin.id).toBe("monthHeader");
  });

  it("has an afterDraw function", () => {
    expect(typeof monthHeaderPlugin.afterDraw).toBe("function");
  });
});
