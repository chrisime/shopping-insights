import { readdir, readFile } from "node:fs/promises";
import { get, type IncomingMessage } from "node:http";
import { brotliDecompressSync, gunzipSync } from "node:zlib";
import { expect, test } from "@playwright/test";

const builtAssets = new URL("../dist/assets/", import.meta.url);
const vendorPattern = /^echarts-vendor-.*\.js$/;
const rendererPattern = /^TrendChartRenderer-.*\.js$/;

const assetName = (url: string) => new URL(url).pathname.split("/").at(-1) ?? "";

const getAsset = async (url: URL, acceptEncoding: string) => {
  const response = await new Promise<IncomingMessage>((resolve, reject) => {
    get(url, { headers: { "Accept-Encoding": acceptEncoding } }, resolve).on("error", reject);
  });
  const chunks: Buffer[] = [];
  for await (const chunk of response) chunks.push(chunk);
  return { status: response.statusCode, headers: response.headers, body: Buffer.concat(chunks) };
};

test("FastAPI serves the production ECharts chunk as Brotli and gzip", async ({ baseURL }) => {
  const vendor = (await readdir(builtAssets)).find((name) => vendorPattern.test(name));
  if (!vendor) throw new Error("ECharts vendor chunk is missing from dist/assets");
  const original = await readFile(new URL(vendor, builtAssets));
  const url = new URL("/assets/" + vendor, baseURL);

  for (const [acceptEncoding, encoding, decompress] of [
    ["br, gzip", "br", brotliDecompressSync],
    ["gzip", "gzip", gunzipSync],
    ["br;q=0.5, gzip;q=1", "gzip", gunzipSync],
  ] as const) {
    const response = await getAsset(url, acceptEncoding);
    expect(response.status).toBe(200);
    expect(response.headers["content-type"]).toContain("javascript");
    expect(response.headers["content-encoding"]).toBe(encoding);
    expect(response.headers.vary).toContain("Accept-Encoding");
    expect(Number(response.headers["content-length"])).toBe(response.body.length);
    expect(response.body.length).toBeLessThan(original.length);
    expect(decompress(response.body).equals(original)).toBe(true);
  }
});

test("Chromium requests ECharts only when the trend tab opens", async ({ page }) => {
  await page.route(/\/ui\/dashboard(?:\?|$)/, (route) =>
    route.fulfill({
      json: {
        title: "Monatsübersicht",
        min_date: "2024-12-31",
        max_date: "2025-01-01",
        sections: [
          {
            kind: "metrics",
            title: "Allgemeine Informationen",
            items: [
              {
                spendings: 21,
                spendings_without_discount: 21,
                receipt_count: 2,
                avg_receipt_amount: 10.5,
                saved_deposit: 0,
                total_savings: 0,
                total_savings_pct: 0,
              },
            ],
          },
          {
            kind: "spending_over_time",
            title: "Ausgaben über Zeit",
            items: [
              { period: "2024-12-31", total_spent: 10, receipt_count: 1 },
              { period: "2025-01-01", total_spent: 11, receipt_count: 1 },
            ],
          },
        ],
      },
    }),
  );

  const chartRequests: string[] = [];
  page.on("request", (request) => {
    const name = assetName(request.url());
    if (vendorPattern.test(name) || rendererPattern.test(name)) chartRequests.push(name);
  });

  await page.goto("/");
  await expect(page.getByText("Ausgaben gesamt", { exact: true })).toBeVisible();
  expect(chartRequests).toEqual([]);

  const vendor = page.waitForResponse((response) => vendorPattern.test(assetName(response.url())));
  const renderer = page.waitForResponse((response) =>
    rendererPattern.test(assetName(response.url())),
  );
  await page.getByTestId("dashboard-tab-spending-over-time").click();

  expect((await vendor).ok()).toBe(true);
  expect((await renderer).ok()).toBe(true);
  await expect(page.getByTestId("trend-bar-chart").locator("svg")).toContainText("Januar 2025");
});
