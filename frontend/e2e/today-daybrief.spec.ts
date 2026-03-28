import { expect, test } from "@playwright/test";
import { bootstrapMockTelegram, expectNoCrash } from "./utils";

type AnalyticsEvent = { event: string; payload: Record<string, unknown> };

async function readAnalytics(page: Parameters<typeof test>[0]["page"]) {
  return page.evaluate(() => (window as Window & typeof globalThis & { __analyticsEvents?: AnalyticsEvent[] }).__analyticsEvents ?? []);
}

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
      profileOverride: {
        full_name: "Debug User",
        birth_date: "2000-01-01",
        subscription_active_until: "2026-04-15T00:00:00.000Z",
      },
      feedOverride: {
        day_brief: {
          version: "day_brief_v1",
          date: "2026-03-27",
          personalization_level: "personalized_v2",
          fallback_mode: false,
          summary: {
            headline: "Держите главный вектор узким и точным.",
            subhead: "День лучше проходит через спокойный темп, короткие решения и мягкую коммуникацию.",
            day_type: "deep_focus",
            tone: "active_structured",
          },
          context: {
            moon_sign: "Овен",
            moon_phase: "Растущая Луна",
            moon_emoji: "🌙",
            aspects_count: 3,
            label: "Луна в Овне · 3 ключевых аспекта",
          },
          scores: [
            { key: "energy", title: "Энергия", value: 74, status: "green", advice: "Используйте ресурс на один приоритетный блок." },
            { key: "money", title: "Деньги", value: 62, status: "yellow", advice: "Проверьте цифры и финальные формулировки." },
            { key: "love", title: "Отношения", value: 58, status: "yellow", advice: "Говорите мягко и не перегружайте переписку." },
            { key: "focus", title: "Фокус", value: 81, status: "green", advice: "Сильнее всего работает глубокая одиночная задача." },
          ],
          windows: [
            { id: "morning", start: "09:00", end: "11:30", label: "Собрать ядро дня", mode: "best", advice: "Закройте главную задачу до обеда." },
            { id: "afternoon", start: "14:00", end: "16:00", label: "Мягкие согласования", mode: "soft", advice: "Перепроверьте договорённости и детали." },
          ],
          best_uses: [
            { id: "best-1", text: "Закрыть один глубокий рабочий блок", impact: "high", timeframe: "morning" },
            { id: "best-2", text: "Провести короткий точный созвон", impact: "medium", timeframe: "afternoon" },
          ],
          risks: [
            { id: "risk-1", text: "Не разгоняйте разговоры в конфликтный тон", impact: "high", timeframe: "all_day" },
            { id: "risk-2", text: "Не распыляйте внимание на параллельные мелочи", impact: "medium", timeframe: "morning" },
          ],
          personalized_factors: [
            { id: "factor-1", label: "Лунный драйв", impact: "medium", category: "lunar", explanation_human: "Утром проще быстро войти в темп и взять инициативу." },
            { id: "factor-2", label: "Коммуникация", impact: "medium", category: "transit_natal", explanation_human: "Лучше работают короткие и ясные сообщения без лишних эмоций." },
          ],
          explainability: {
            confidence: 0.82,
            birth_time_used: true,
            factor_count: 6,
            timing_precision: "exact",
            top_signal_source: "transit_natal",
            explanation_depth: "standard",
          },
          premium: {
            subscription_active: true,
            subscription_active_until: "2026-04-15",
            days_left: 19,
            show_upgrade_cta: false,
            show_resume_banner: false,
          },
          cta: {
            primary: { type: "open_week", label: "Открыть неделю", href: "/week" },
            secondary: { type: "open_history", label: "История разборов", href: "/reports/history" },
          },
        },
      },
    });

    await page.route("**/api/analytics/**", async (route) => {
      await route.fulfill({ status: 204, body: "" });
    });
  });

  test("renders today from DayBrief DTO and emits telemetry", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("home-feed-page")).toBeVisible();
    await expect(page.getByTestId("today-verdict")).toContainText("Держите главный вектор узким и точным.");
    await expect(page.getByTestId("today-day-mode")).toContainText("Глубокий фокус");
    await expect(page.getByTestId("today-windows")).toBeVisible();
    await expect(page.getByTestId("today-actions")).toBeVisible();
    await expect(page.getByTestId("today-risks")).toBeVisible();
    await expect(page.getByTestId("today-explainability")).toContainText("Уверенность");
    await expect(page.getByTestId("today-cta-panel")).toBeVisible();
    await expect(page.getByTestId("today-cta-week")).toContainText("Открыть неделю");
    await expect(page.getByTestId("today-cta-premium")).toContainText("История разборов");

    await page.getByTestId("today-score-energy").click();
    await page.waitForTimeout(200);

    const analytics = await readAnalytics(page);
    expect(analytics.some((event) => event.event === "home.feed_mock_state" || event.event === "today.brief_view")).toBeTruthy();
    expect(analytics.some((event) => event.event === "today.score_tap")).toBeTruthy();
  });

  test("uses temporary legacy adapter fallback", async ({ page }) => {
    await bootstrapMockTelegram(page, {
      feedState: "fallback",
      profileOverride: {
        full_name: "Debug User",
        birth_date: "2000-01-01",
      },
      feedOverride: {
        date: "Сегодня",
        moon_sign: "Рыбы",
        moon_phase: "Фоновый режим",
        moon_emoji: "🌙",
        general_vibe: "Лучше сохранить мягкий ритм и не перегружать день решениями.",
        traffic_lights: { health: "yellow", money: "yellow", love: "red" },
        fast_hits: [{ transit: "Moon", natal: "Mars", type: "Квадрат", summary: "Не форсируйте резкие разговоры" }],
        personalization_level: "fallback",
      },
    });

    await page.goto("/");
    await expect(page.getByTestId("today-verdict")).toBeVisible();
    await expect(page.getByTestId("today-windows")).toBeVisible();
    await expect(page.getByTestId("today-cta-panel")).toBeVisible();
  });
});
