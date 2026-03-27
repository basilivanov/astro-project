import { expect, test } from "@playwright/test";
import { bootstrapMockTelegram } from "./utils";

test("debug week route render", async ({ page }) => {
  const logs: string[] = [];
  await bootstrapMockTelegram(page, {
    feedState: "ready",
    profileOverride: { full_name: "Debug User", birth_date: "2000-01-01" },
  });
  await page.addInitScript(() => {
    (window as Window & { MOCK_WEEK_REPORT_OVERRIDE?: unknown }).MOCK_WEEK_REPORT_OVERRIDE = {
      report: { id: "week-1", report_type: "week_forecast", status: "completed" },
      chunks: [],
    };
  });
  page.on("console", (msg) => {
    if (msg.type() === "error") logs.push(`console:${msg.text()}`);
  });
  page.on("pageerror", (err) => logs.push(`pageerror:${err.message}`));
  await page.goto("/week?mock=1", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);
  console.log(`URL=${page.url()}`);
  console.log(`LOGS=${JSON.stringify(logs)}`);
  console.log(`BODY=${await page.locator("body").innerText()}`);
  await expect(page.locator("body")).toBeVisible();
});
