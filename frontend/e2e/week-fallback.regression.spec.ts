import { expect, test, type Page, type Route } from "@playwright/test";

import { bootstrapMockTelegram, expectNoCrash } from "./utils";

type TelemetryEvent = {
  event: string;
  payload: Record<string, unknown>;
};

async function installTelemetryCapture(page: Page, telemetry: TelemetryEvent[]) {
  await page.route("**/api/analytics/**", async (route: Route) => {
    const request = route.request();
    const bodyText = request.postData() ?? "";

    try {
      const parsed = JSON.parse(bodyText);
      const batch = Array.isArray(parsed?.events) ? parsed.events : parsed ? [parsed] : [];
      for (const item of batch) {
        telemetry.push({
          event: typeof item?.event === "string" ? item.event : typeof item?.event_name === "string" ? item.event_name : "unknown",
          payload: (item ?? {}) as Record<string, unknown>,
        });
      }
    } catch {}

    await route.fulfill({ status: 204, body: "" });
  });
}

async function waitForTelemetry(telemetry: TelemetryEvent[], eventName: string) {
  await expect
    .poll(() => telemetry.some((item) => item.event === eventName), { timeout: 15000 })
    .toBe(true);
  return telemetry.find((item) => item.event === eventName);
}

test.describe("VM-WEEK-FALLBACK", () => {
  test("renders week fetch fallback safely and emits success telemetry", async ({ page }) => {
    const telemetry: TelemetryEvent[] = [];
    await installTelemetryCapture(page, telemetry);
    await bootstrapMockTelegram(page);

    const reportId = "week-fallback-report";
    await page.route("**/api/reports/**", async (route) => {
      const url = route.request().url();

      if (url.includes("/api/reports/my?")) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            { id: reportId, report_type: "week_forecast", status: "completed" },
          ]),
        });
        return;
      }

      if (url.includes(`/api/reports/${reportId}`)) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            report: { id: reportId, report_type: "week_forecast", status: "completed" },
            chunks: [
              {
                id: "week-strategy",
                section: "week_strategy",
                title: "Стратегия недели",
                content: "Неделя требует спокойного темпа и аккуратной расстановки приоритетов.",
              },
            ],
          }),
        });
        return;
      }

      await route.continue();
    });

    await page.goto("/week");
    await expectNoCrash(page);
    await expect(page.getByTestId("week-page")).toBeVisible();
    await expect(page.getByTestId("week-map-surface")).toBeVisible();
    await expect(page.getByTestId("week-day-grid")).toBeVisible();
    await expect(page.getByTestId("week-primary-cta")).toBeVisible();
    await expect(page.getByTestId("week-deep-sections")).toBeVisible();
    await expect(page.getByTestId("week-deep-sections")).toContainText(
      "Неделя требует спокойного темпа и аккуратной расстановки приоритетов.",
    );
    await expect(page.getByTestId("week-deep-sections")).not.toContainText("Короткая версия раздела");
    await expect(page.getByTestId("week-fallback-note")).toBeVisible();
    await expect(page.getByTestId("week-fallback-note")).toContainText("сокращённая версия недели");
    await expect(page.getByTestId("week-fallback-note")).not.toContainText(/fallback|weekbrief|legacy|week_map/i);
    await expect(page.getByTestId("week-map-surface")).not.toContainText(/legacy|fallback|week_map|weekbrief|headline|markdown|weekly report|compatibility/i);

    const briefView = await waitForTelemetry(telemetry, "week.brief_view");

    expect(briefView?.payload.surface).toBe("week");
    expect(briefView?.payload.block).toBe("WEEK_BRIEF_VIEW");
    expect(briefView?.payload.status).toBe("ready");
    expect(briefView?.payload.sections_count).toBe(1);
    expect(briefView?.payload.correlation_id).toBeTruthy();
  });
});
