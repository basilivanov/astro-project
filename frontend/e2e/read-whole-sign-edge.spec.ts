import { expect, test, type ConsoleMessage } from "@playwright/test";

import { buildCanonicalWeekPersonaPack } from "./fixtures/canonical-personas";
import { bootstrapMockTelegram, expectNoCrash } from "./utils";

const canonicalPersona = buildCanonicalWeekPersonaPack("CF-WS-002-whole-sign-edge");
const canonicalReportId = canonicalPersona.week!.reportId;

function attachConsoleHygiene(page: Parameters<typeof test>[0]["page"], logs: string[]) {
  page.on("console", (msg: ConsoleMessage) => {
    if (msg.type() === "error") {
      logs.push(`[console:error] ${msg.text()}`);
    }
  });
  page.on("pageerror", (error) => {
    logs.push(`[pageerror] ${error.message}`);
  });
}

test.describe("Read whole-sign edge continuity", () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page, {
      profileOverride: canonicalPersona.profile,
    });

    await page.route(`**/api/reports/${canonicalReportId}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        json: {
          report: canonicalPersona.week!.report,
          persona_pack: {
            fixture_id: "CF-WS-002-whole-sign-edge",
            manifest_id: "canonical-astrology-fixtures-v1",
            scenario_label: "whole-sign-edge",
          },
          chunks: [
            {
              id: "safety",
              section: "house_system_safety",
              title: "Астрологическая опора",
              content: "Whole Sign safe mode keeps the interpretation readable at high latitude.",
            },
          ],
        },
      });
    });
  });

  test("shows whole-sign safe mode as visible continuity truth without crashing", async ({ page }) => {
    const logs: string[] = [];
    attachConsoleHygiene(page, logs);

    await page.goto(`/read/${canonicalReportId}?mock=1`);

    await expectNoCrash(page);
    await expect(page.getByTestId("read-known-time-panel")).toBeVisible();
    await expect(page.getByText("Safe mode домов сохранён")).toBeVisible();
    await expect(page.getByTestId("read-known-time-evidence")).toContainText("Safe mode: Whole Sign");
    await expect(page.getByTestId("read-known-time-evidence")).toContainText("CF-WS-002-whole-sign-edge");
    await expect(page.getByTestId("read-known-time-summary")).toContainText("Today, Week и Read");
    expect(logs, `Found console or page errors on read whole-sign edge path: ${logs.join(", ")}`).toHaveLength(0);
  });
});
