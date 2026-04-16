import { expect, test, type ConsoleMessage, type Page, type TestInfo } from "@playwright/test";

import { buildCanonicalWeekPersonaPack } from "./fixtures/canonical-personas";
import { bootstrapMockTelegram, expectNoCrash } from "./utils";

type AnalyticsEvent = {
  event: string;
  payload: Record<string, unknown>;
};

const canonicalPersona = buildCanonicalWeekPersonaPack("CF-BE-001-baseline-exact-time");
const canonicalWeek = canonicalPersona.week!;

async function waitForAnalyticsEvent(analytics: AnalyticsEvent[], eventName: string) {
  await expect
    .poll(
      async () => analytics.some((item) => item.event === eventName),
      { timeout: 5000 },
    )
    .toBeTruthy();
}

function attachConsoleHygiene(page: Page, logs: string[]) {
  page.on("console", (msg: ConsoleMessage) => {
    if (msg.type() !== "error") {
      return;
    }
    const text = msg.text();
    if (text.includes("net::ERR_NETWORK_CHANGED") || text === "Event") {
      return;
    }
    if (text.includes("data-runtime-badge-event")) {
      return;
    }
    logs.push(`[console:error] ${text}`);
  });
  page.on("pageerror", (error) => {
    logs.push(`[pageerror] ${error.message}`);
  });
}

async function captureVisualEvidence(page: Page, testInfo: TestInfo, filename: string) {
  const screenshotPath = testInfo.outputPath(filename);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await testInfo.attach(filename, { path: screenshotPath, contentType: "image/png" });
}

async function installCanonicalWeekMocks(page: Page, analytics: AnalyticsEvent[]) {
  await bootstrapMockTelegram(page, {
    profileOverride: canonicalPersona.profile,
    weekBriefOverride: canonicalWeek.weekBrief,
    weekMapOverride: canonicalWeek.weekMap,
  });

  await page.route("**/api/analytics/**", async (route) => {
    const body = route.request().postDataJSON();
    const batch = Array.isArray(body?.events) ? body.events : body ? [body] : [];

    analytics.push(
      ...batch.map((item) => ({
        event: String(item?.event ?? item?.event_name ?? ""),
        payload: typeof item?.payload === "object" && item?.payload ? item.payload as Record<string, unknown> : {},
      })),
    );

    await route.fulfill({ status: 204, body: "" });
  });

  await page.route("**/api/reports/my?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      json: [canonicalWeek.report],
    });
  });

  await page.route(`**/api/reports/${canonicalWeek.reportId}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      json: {
        report: canonicalWeek.report,
        week_brief: canonicalWeek.weekBrief,
        week_brief_envelope: { status: "ready", data: canonicalWeek.weekBrief, message: null },
        week_map: canonicalWeek.weekMap,
        chunks: [
          {
            id: "strategy",
            section: "week_strategy",
            title: "Стратегия недели",
            content: "# Стратегия недели\n\nДержите ритм спокойным и возвращайтесь ко второму проходу.",
          },
        ],
      },
    });
  });
}

test.describe("Canonical frontend adoption wave 2", () => {
  test("protects canonical Ava Meridian Today-to-Week continuity without brittle copy coupling", async ({ page }, testInfo) => {
    const logs: string[] = [];
    const analytics: AnalyticsEvent[] = [];
    attachConsoleHygiene(page, logs);
    await installCanonicalWeekMocks(page, analytics);

    await page.goto("/week?mock=1");

    await expectNoCrash(page);
    await expect(page.getByTestId("week-page")).toBeVisible();
    await expect(page.getByTestId("week-map-surface")).toContainText("Настройка темпа и фиксация результата");
    await expect(page.getByTestId("week-domain-panel")).toBeVisible();
    await expect(page.getByTestId("week-day-strip")).toBeVisible();
    await expect(page.getByTestId("week-day-strip").locator('article[data-testid^="week-day-strip-card-"]')).toHaveCount(7);
    await expect(page.getByTestId("week-domain-panel")).toContainText("Работа и деньги");
    await expect(page.getByTestId("week-actions-list")).toContainText("Делайте один приоритетный ход за раз.");
    await expect(page.getByTestId("week-risks-list")).toContainText("Не пытайтесь закрыть то, что ещё не дозрело.");
    await expect(page.getByTestId("week-explainability-panel")).toContainText("Почему неделя держится именно так");
    await expect(page.getByTestId("week-explainability-panel")).toContainText("Учтено точное время рождения");
    await expect(page.getByTestId("week-deep-sections")).toContainText("Стратегия недели");
    await expect(page.getByTestId("week-primary-cta")).toContainText("Открыть полный отчёт");
    await expect(page.getByText("Персональной недели пока нет")).toHaveCount(0);
    await expect(page.getByTestId("report-fallback-card")).toHaveCount(0);
    await captureVisualEvidence(page, testInfo, "canonical-week-surface.png");

    await page.getByTestId("week-day-strip-card-1").click();
    await waitForAnalyticsEvent(analytics, "week.brief_view");
    await waitForAnalyticsEvent(analytics, "week.day_card_click");
    const navigationPromise = page.waitForURL(new RegExp(`/read/${canonicalWeek.reportId}$`));
    const primaryCtaEventPromise = waitForAnalyticsEvent(analytics, "week.open_full_report_click");
    await page.getByTestId("week-primary-cta").click();
    await primaryCtaEventPromise;
    await navigationPromise;
    expect(logs, `Found console or page errors on canonical /week continuity path: ${logs.join(", ")}`).toHaveLength(0);
  });
});
