import { expect, test } from "@playwright/test";
import { attachRuntimeErrorGuards, bootstrapMockTelegram, expectNoCrash, expectNoRuntimeErrors } from "./utils";
import { buildCanonicalTodayPersonaPack } from "./fixtures/canonical-personas";

type AnalyticsEvent = { event: string; payload: Record<string, unknown> };

async function readAnalytics(page: Parameters<typeof test>[0]["page"]) {
  return page.evaluate(() => (window as Window & typeof globalThis & { __analyticsEvents?: AnalyticsEvent[] }).__analyticsEvents ?? []);
}

async function bootstrapTelegramMobile(page: Parameters<typeof test>[0]["page"], options?: Parameters<typeof bootstrapMockTelegram>[1]) {
  await page.setViewportSize({ width: 390, height: 844 });
  await bootstrapMockTelegram(page, options);
}

async function mobileActivate(locator: ReturnType<Parameters<typeof test>[0]["page"]["locator"]>) {
  await locator.dispatchEvent('touchstart');
  await locator.dispatchEvent('touchend');
  await locator.click();
}

const canonicalPersona = buildCanonicalTodayPersonaPack("CF-BE-001-baseline-exact-time");

test.describe("Today DayBrief surface", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      (window as Window & typeof globalThis & { __analyticsEvents?: AnalyticsEvent[] }).__analyticsEvents = [];
      const originalFetch = window.fetch.bind(window);
      window.fetch = async (input, init) => {
        const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
        if (url.includes("/api/analytics")) {
          const bodyText = typeof init?.body === "string" ? init.body : "";
          try {
            const parsed = JSON.parse(bodyText);
            const batch = Array.isArray(parsed?.events) ? parsed.events : parsed ? [parsed] : [];
            for (const item of batch) {
              const payload = typeof item?.properties === "object" && item.properties
                ? item.properties
                : typeof item?.payload === "object" && item.payload
                  ? item.payload
                  : {};
              (window as Window & typeof globalThis & { __analyticsEvents: AnalyticsEvent[] }).__analyticsEvents.push({
                event: typeof item?.event === "string" ? item.event : typeof item?.event_name === "string" ? item.event_name : "unknown",
                payload: typeof payload?.payload === "object" && payload.payload ? payload.payload as Record<string, unknown> : payload as Record<string, unknown>,
              });
            }
          } catch {}
        }
        return originalFetch(input, init);
      };
    });

    await bootstrapMockTelegram(page, {
      feedState: "ready",
      profileOverride: canonicalPersona.profile,
      feedOverride: canonicalPersona.feed,
    });
  });

  test("renders stable canonical persona brief without runtime errors", async ({ page }) => {
    const hygiene = await attachRuntimeErrorGuards(page);
    await bootstrapTelegramMobile(page);
    await page.goto("/");

    await expectNoCrash(page);
    await expect(page.getByTestId("home-feed-page")).toBeVisible();
    await expect(page.getByTestId("today-verdict")).toContainText("Держите главный вектор узким и точным.");
    await expect(page.getByTestId("today-moon-context")).toContainText("Импульсный лунный фон для коротких и точных решений.");
    await expect(page.getByTestId("today-score-energy")).toContainText("Энергия");
    await expect(page.getByTestId("today-score-focus")).toContainText("Фокус");
    await expect(page.getByTestId("today-windows")).toContainText("Собрать ядро дня");
    await expect(page.getByTestId("today-actions")).toContainText("Закрыть один глубокий рабочий блок");
    await expect(page.getByTestId("today-risks")).toContainText("Не разгоняйте разговоры в конфликтный тон");
    await expect(page.getByTestId("today-explainability")).toContainText("Почему такой день");
    await expect(page.getByTestId("today-cta-week")).toContainText("Открыть неделю");
    await expect(page.getByTestId("today-cta-premium")).toContainText("История разборов");
    await expect(page.getByTestId("home-feed-page")).not.toContainText(/\bsignal_only\b/i);
    await expect(page.getByTestId("home-feed-page")).not.toContainText(/\bstructured_value\b/i);
    await expect(page.getByTestId("home-feed-page")).not.toContainText(/\bgreen\b/i);
    await expectNoRuntimeErrors(hygiene, "today canonical persona render");
    hygiene.dispose();
  });

  test("score disclosure hides global factor fallback for canonical persona", async ({ page }) => {
    await bootstrapTelegramMobile(page);
    await page.goto("/");

    const scoreCard = page.getByTestId("today-score-energy");
    await expect(scoreCard).toContainText("72");
    await scoreCard.getByRole("button", { name: /Энергия: 72/ }).click();

    const scoreDisclosure = scoreCard.getByTestId("today-score-details-energy");
    await expect(scoreDisclosure).toHaveAttribute("open", "");
    await expect(scoreDisclosure.locator("summary")).toContainText("Как открыть разбор");
    await expect(scoreDisclosure).toContainText("Нажмите на карточку, чтобы открыть подробный разбор этой сферы, когда он доступен в персональной сводке.");
    await expect(scoreDisclosure).not.toContainText("Лунный драйв");
    await expect(scoreDisclosure).not.toContainText("Утром проще быстро войти в темп и взять инициативу.");
    await expect(scoreDisclosure).not.toContainText(/\bsignal_only\b/i);
    await expect(scoreDisclosure).not.toContainText(/\bstructured_value\b/i);
  });

  test("week CTA preserves Today to Week continuity for canonical persona", async ({ page }) => {
    await bootstrapTelegramMobile(page);
    await page.goto("/");
    await expectNoCrash(page);
    await expect(page.getByTestId("today-cta-panel")).toBeVisible();

    await page.route("**/api/reports/my?*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{ id: "mock-week", report_type: "week_forecast", status: "completed" }]),
      });
    });
    await page.route("**/api/reports/mock-week", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ report: { id: "mock-week", report_type: "week_forecast", status: "completed" }, chunks: [] }),
      });
    });

    await mobileActivate(page.getByTestId("today-cta-week"));
    await expect(page).toHaveURL(/\/week(?:\?|$)/);
    await expect(page.getByTestId("week-page")).toBeVisible();
  });

  test("emits Today analytics with canonical persona score tap and CTA", async ({ page }) => {
    await bootstrapTelegramMobile(page);
    await page.route("**/api/reports/my?*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{ id: "mock-week", report_type: "week_forecast", status: "completed" }]),
      });
    });
    await page.route("**/api/reports/mock-week", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ report: { id: "mock-week", report_type: "week_forecast", status: "completed" }, chunks: [] }),
      });
    });

    await page.goto("/");
    await page.getByTestId("today-score-energy").getByRole("button", { name: /Энергия: 72/ }).click();
    await mobileActivate(page.getByTestId("today-cta-week"));

    const events = await readAnalytics(page);
    expect(events.some((item) => item.event === "today.score_tap")).toBeTruthy();
    expect(events.some((item) => item.event === "today.cta_click" || item.event === "today.cta_secondary_click")).toBeTruthy();
  });
});
