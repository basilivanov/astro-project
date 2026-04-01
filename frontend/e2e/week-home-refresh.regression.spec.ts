import { expect, test, type ConsoleMessage, type Page } from "@playwright/test";
import { bootstrapMockTelegram, expectNoCrash } from "./utils";

type AnalyticsEvent = {
  event: string;
  payload: Record<string, unknown>;
};

const reportId = "week-brief-regression-report";

const mockWeekBrief = {
  version: "week_brief_v1",
  week_start: "2026-03-23",
  week_end: "2026-03-29",
  personalization_level: "full",
  fallback_mode: false,
  status: "ready",
  summary: {
    headline: "Неделя просит точной сборки и спокойного темпа",
    subhead: "Лучше всего работают короткие циклы, уточнения и своевременный возврат ко второму проходу.",
    week_type: "balance",
    theme: "Настройка темпа и фиксация результата",
  },
  day_cards: [
    { date: "2026-03-23", weekday: "mon", mode: "green", score: 82, headline: "Соберите приоритеты", best_for: ["Планирование"], avoid: ["Суета"], peak_window_label: "до 14:00" },
    { date: "2026-03-24", weekday: "tue", mode: "yellow", score: 63, headline: "Проверяйте стыки", best_for: ["Уточнения"], avoid: ["Конфликты"] },
    { date: "2026-03-25", weekday: "wed", mode: "red", score: 34, headline: "Не форсируйте решения", best_for: ["Рутина"], avoid: ["Сделки"] },
    { date: "2026-03-26", weekday: "thu", mode: "yellow", score: 58, headline: "Вернитесь ко второму проходу", best_for: ["Редактура"], avoid: ["Поспешность"] },
    { date: "2026-03-27", weekday: "fri", mode: "green", score: 80, headline: "Закрепляйте результат", best_for: ["Презентации"], avoid: ["Перегруз"] },
    { date: "2026-03-28", weekday: "sat", mode: "yellow", score: 55, headline: "Снижайте темп", best_for: ["Быт"], avoid: ["Шум"] },
    { date: "2026-03-29", weekday: "sun", mode: "green", score: 76, headline: "Спокойно соберите следующую неделю", best_for: ["План"], avoid: ["Рывок"] },
  ],
  domains: [
    { key: "work_money", title: "Работа и деньги", status: "green", value: 78, headline: "Лучший домен недели", advice: "Фиксируйте договорённости письменно." },
    { key: "relationships", title: "Отношения", status: "yellow", value: 61, headline: "Нужны уточнения", advice: "Не оставляйте двусмысленность." },
    { key: "energy", title: "Энергия", status: "yellow", value: 57, headline: "Берегите ресурс", advice: "Оставляйте окна на восстановление." },
  ],
  best_uses: [
    { id: "a1", text: "Делайте один приоритетный ход за раз." },
    { id: "a2", text: "Возвращайтесь ко второму проходу вместо давления." },
    { id: "a3", text: "Сверяйте ожидания в переговорах заранее." },
  ],
  risks: [
    { id: "r1", text: "Не пытайтесь закрыть то, что ещё не дозрело." },
    { id: "r2", text: "Не распыляйтесь на параллельные обещания." },
  ],
  major_factors: [
    { id: "f1", label: "Фон недели", impact: "high", explanation_human: "Главный выигрыш приходит через точную фиксацию результата." },
    { id: "f2", label: "Тайминг", impact: "medium", explanation_human: "Лучше работают вторые проходы и редактуры, чем силовой рывок." },
  ],
  deep_sections: [
    {
      id: "strategy",
      slug: "week_strategy",
      title: "Стратегия недели",
      summary: "Собирайте неделю в коротких циклах.",
      body_markdown: "# Стратегия недели\n\nДержите ритм спокойным и возвращайтесь ко второму проходу, когда задача не закрывается с первого раза.",
      is_primary: true,
      order: 0,
    },
  ],
  explainability: { confidence: 0.81, birth_time_used: true, factor_count: 4, top_signal_source: "transit_natal" },
  cta: { primary: { type: "custom", label: "Открыть полный отчёт", href: `/read/${reportId}` } },
  report_ref: { report_id: reportId, report_type: "week_forecast", source_status: "completed" },
};

function mockWeekMap() {
  return {
    thesis: "Настройка темпа и фиксация результата",
    theme: "Лучше всего работают короткие циклы",
    day_cards: mockWeekBrief.day_cards?.map((card) => ({
      date: card.date,
      weekday: card.weekday,
      mode: card.mode,
      headline: card.headline,
      best_for: card.best_for,
      avoid: card.avoid,
      score: (card.score ?? 50) / 100,
    })),
    domains: {
      work: 78,
      relationships: 61,
      energy: 57,
      focus: 74,
    },
  };
}

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
    if (msg.type() === "error") {
      logs.push(`[console:error] ${msg.text()}`);
    }
  });
  page.on("pageerror", (error) => {
    logs.push(`[pageerror] ${error.message}`);
  });
}

async function installWeekReadyMocks(page: Page) {
  await bootstrapMockTelegram(page, {
    weekBriefOverride: mockWeekBrief,
    weekMapOverride: mockWeekMap(),
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
      json: [{ id: reportId, report_type: "week_forecast", status: "completed" }],
    });
  });

  await page.route(`**/api/reports/${reportId}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      json: {
        report: { id: reportId, report_type: "week_forecast", status: "completed" },
        week_brief: mockWeekBrief,
        week_brief_envelope: { status: "ready", data: mockWeekBrief, message: null },
        week_map: mockWeekMap(),
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

  await page.route("**/api/billing/sessions/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      json: {
        id: "session-week-refresh",
        status: "succeeded",
        report_type: "week_forecast",
        checkout_token: "week-checkout-token",
        return_path: "/create?type=week_forecast&checkout=week-checkout-token&mock=1&runtime=1",
        resumed_report_id: reportId,
      },
    });
  });
}

test.describe("VM-WEEK-P0", () => {
  test("guards /week route load, CTA flow, happy path, and console hygiene", async ({ page }) => {
    const logs: string[] = [];
    attachConsoleHygiene(page, logs);
    await installWeekReadyMocks(page);

    await page.goto("/week?mock=1&runtime=1&checkout=week-checkout-token");

    await expectNoCrash(page);
    await expect(page.getByTestId("week-page")).toBeVisible();
    await expect(page.getByTestId("catalog-checkout-resume")).toBeVisible();
    await expect(page.getByTestId("week-map-surface")).toContainText("Настройка темпа и фиксация результата");
    await expect(page.getByTestId("week-day-grid")).toBeVisible();
    await expect(page.getByTestId("week-domain-panel")).toContainText("Работа и деньги");
    await expect(page.getByTestId("week-actions-list")).toContainText("Делайте один приоритетный ход за раз");
    await expect(page.getByTestId("week-risks-list")).toContainText("Не пытайтесь закрыть то, что ещё не дозрело");
    await expect(page.getByTestId("week-primary-cta")).toBeVisible();

    await page.getByTestId("week-day-card-1").click();
    await page.getByTestId("week-primary-cta").click();
    await expect(page).toHaveURL(new RegExp(`/read/${reportId}$`));

    const analytics = await readAnalytics(page);
    expect(analytics.some((item) => item.event === "week.brief_view")).toBeTruthy();
    expect(analytics.some((item) => item.event === "week.day_card_click")).toBeTruthy();
    expect(analytics.some((item) => item.event === "week.open_full_report_click")).toBeTruthy();
    expect(analytics.some((item) => item.event === "catalog.checkout_resume_ready")).toBeTruthy();
    expect(analytics.some((item) => item.event === "catalog.checkout_resume_success")).toBeTruthy();
    expect(logs, `Found console or page errors on /week happy path: ${logs.join(", ")}`).toHaveLength(0);
  });

  test("guards /week no-report fallback without crash or dirty console", async ({ page }) => {
    const logs: string[] = [];
    attachConsoleHygiene(page, logs);
    await bootstrapMockTelegram(page);

    await page.route("**/api/analytics/**", async (route) => {
      await route.fulfill({ status: 204, body: "" });
    });

    await page.route("**/api/reports/my?**", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", json: [] });
    });

    await page.goto("/week?mock=1");

    await expectNoCrash(page);
    await expect(page.getByTestId("week-page")).toBeVisible();
    await expect(page.getByTestId("week-primary-cta")).toBeVisible();
    await expect(page.getByTestId("week-primary-cta")).toHaveAttribute("href", /\/create\?type=week_forecast/);
    await page.getByTestId("week-primary-cta").click();
    await expect(page).toHaveURL(/\/create\?type=week_forecast/);
    expect(logs, `Found console or page errors on /week no-report path: ${logs.join(", ")}`).toHaveLength(0);
  });
});
