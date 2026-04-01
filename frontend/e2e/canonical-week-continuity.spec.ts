import { expect, test, type ConsoleMessage, type Page } from "@playwright/test";

import { buildCanonicalWeekPersonaPack } from "./fixtures/canonical-personas";
import { bootstrapMockTelegram, expectNoCrash } from "./utils";

type AnalyticsEvent = {
  event: string;
  payload: Record<string, unknown>;
};

const canonicalPersona = buildCanonicalWeekPersonaPack("CF-BE-001-baseline-exact-time");
const canonicalWeek = canonicalPersona.week!;

async function readAnalytics(page: Page): Promise<AnalyticsEvent[]> {
  return page.evaluate(() => {
    return ((window as Window & typeof globalThis & { __astroAnalyticsEvents?: AnalyticsEvent[] }).__astroAnalyticsEvents ?? []).map((item) => ({
      event: item.event,
      payload: item.payload ?? {},
    }));
  });
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
    logs.push(`[console:error] ${text}`);
  });
  page.on("pageerror", (error) => {
    logs.push(`[pageerror] ${error.message}`);
  });
}

async function installCanonicalWeekMocks(page: Page) {
  await bootstrapMockTelegram(page, {
    profileOverride: canonicalPersona.profile,
    weekBriefOverride: canonicalWeek.weekBrief,
    weekMapOverride: canonicalWeek.weekMap,
  });

  await page.addInitScript(() => {
    (window as Window & typeof globalThis & { __astroAnalyticsEvents?: AnalyticsEvent[] }).__astroAnalyticsEvents = [];
  });

  await page.route("**/api/analytics/**", async (route) => {
    const body = route.request().postDataJSON();
    const batch = Array.isArray(body?.events) ? body.events : body ? [body] : [];

    await page.evaluate((events) => {
      const win = window as Window & typeof globalThis & { __astroAnalyticsEvents?: AnalyticsEvent[] };
      win.__astroAnalyticsEvents = [...(win.__astroAnalyticsEvents ?? []), ...events];
    }, batch);

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
  test("protects canonical Ava Meridian Today-to-Week continuity without brittle copy coupling", async ({ page }) => {
    const logs: string[] = [];
    attachConsoleHygiene(page, logs);
    await installCanonicalWeekMocks(page);

    await page.goto("/week?mock=1");

    await expectNoCrash(page);
    await expect(page.getByTestId("week-page")).toBeVisible();
    await expect(page.getByTestId("week-map-surface")).toContainText("Настройка темпа и фиксация результата");
    await expect(page.getByTestId("week-day-grid")).toBeVisible();
    await expect(page.getByTestId("week-domain-panel")).toContainText("Работа и деньги");
    await expect(page.getByTestId("week-actions-list")).toContainText("Делайте один приоритетный ход за раз.");
    await expect(page.getByTestId("week-risks-list")).toContainText("Не пытайтесь закрыть то, что ещё не дозрело.");
    await expect(page.getByTestId("week-explainability-panel")).toContainText("Почему карта именно такая");
    await expect(page.getByTestId("week-explainability-panel")).toContainText("Учтено точное время рождения");
    await expect(page.getByTestId("week-primary-cta")).toContainText("Открыть полный отчёт");

    await page.getByTestId("week-day-card-1").click();
    await page.getByTestId("week-primary-cta").click();
    await expect(page).toHaveURL(new RegExp(`/read/${canonicalWeek.reportId}$`));

    const analytics = await readAnalytics(page);
    expect(analytics.some((item) => item.event === "week.brief_view")).toBeTruthy();
    expect(analytics.some((item) => item.event === "week.day_card_click")).toBeTruthy();
    expect(analytics.some((item) => item.event === "week.open_full_report_click")).toBeTruthy();
    expect(logs, `Found console or page errors on canonical /week continuity path: ${logs.join(", ")}`).toHaveLength(0);
  });
});
