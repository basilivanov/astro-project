import { expect, test } from "@playwright/test";

import {
  attachConsoleAndPageErrors,
  bootstrapSignedTelegram,
  expectNoCrash,
  expectNoRouteHygieneIssues,
  mockCommonApis,
} from "./utils";
async function seedSignedTodayProfile(page: import("@playwright/test").Page, initData: string, profile: Record<string, unknown>) {
  const response = await page.request.put("/api/users/me", {
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Auth": initData,
    },
    data: profile,
  });

  expect(response.ok()).toBeTruthy();
}

const canonicalTodayFeed = {
  day_brief: {
    version: "day_brief_canon_v1",
    status: "complete",
    date: "2026-04-10",
    personalization_level: "personalized_v2",
    hero: {
      title: "День лучше держать собранным и точным.",
      subtitle: "Главный результат приходит через один приоритет и спокойный темп.",
      day_type: "deep_focus",
      tone: "active_structured",
    },
    domains: {
      energy: { key: "energy", title: "Тонус", score_status: "complete", score: 72, status: "green", description_status: "complete", description: "Ресурс лучше раскрывается в ровном ритме без лишних рывков.", why_status: "complete", why_astro_text: "Твой Марс сегодня собирает энергию в последовательное действие, а лунный фон поддерживает телесный ритм.", evidence_refs: [] },
      money: { key: "money", title: "Работа и деньги", score_status: "complete", score: 62, status: "yellow", description_status: "complete", description: "Рабочие и денежные вопросы лучше вести через один главный приоритет и проверку цифр.", why_status: "complete", why_astro_text: "Твой 2-й дом денег и личной цены вопроса сейчас требует точных формулировок и внимательности к условиям.", evidence_refs: [] },
      love: { key: "love", title: "Чувства", score_status: "complete", score: 58, status: "yellow", description_status: "complete", description: "Контакт сегодня держится лучше на мягком тоне и паузе перед ответом.", why_status: "complete", why_astro_text: "Твоя Венера звучит мягче обычного, поэтому бережная подача и короткая честная реплика работают лучше давления.", evidence_refs: [] },
      focus: { key: "focus", title: "Фокус", score_status: "complete", score: 81, status: "green", description_status: "complete", description: "Один глубокий блок даст больше результата, чем распыление на мелочи.", why_status: "complete", why_astro_text: "Твой Меркурий сегодня лучше работает в одной линии, а фон дня усиливает концентрацию на главной задаче.", evidence_refs: [] },
    },
    premium: {
      subscription_active: true,
      subscription_active_until: "2026-05-01",
      days_left: 21,
      show_upgrade_cta: false,
      show_resume_banner: false,
    },
    cta: {
      primary: { type: "open_week", label: "Смотреть неделю", href: "/week" },
      secondary: { type: "ask_question", label: "Задать вопрос", href: "/question" },
    },
  },
};

const canonicalTodayProfile = {
  full_name: "Signed Today",
  birth_date: "1992-08-14",
  birth_time: "06:32",
  birth_place: "London, UK",
  timezone: "Europe/London",
  subscription_active_until: "2026-04-15T00:00:00.000Z",
};

test.describe("telegram signed auth lane", () => {
  test("loads Today authenticated content via signed auth against real backend", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);
    const runtime = await bootstrapSignedTelegram(page, {
      user: {
        id: 45454545,
        first_name: "Signed",
        last_name: "Today",
        username: "signed_today",
        language_code: "ru",
      },
    });

    await mockCommonApis(page);

    const profileHeaders: string[] = [];
    const feedHeaders: string[] = [];

    await page.route("**/api/users/me", async (route) => {
      profileHeaders.push(route.request().headers()["x-telegram-auth"] ?? "");
      await route.continue();
    });

    await page.route("**/api/feed/today", async (route) => {
      feedHeaders.push(route.request().headers()["x-telegram-auth"] ?? "");
      await route.continue();
    });

    await seedSignedTodayProfile(page, runtime.initData, {
      full_name: "Signed Today",
      birth_date: "1992-08-14",
      birth_time: "06:32",
      birth_time_known: true,
      birth_place: "London, UK",
      birth_lat: 51.5074,
      birth_lon: -0.1278,
      birth_timezone: "Europe/London",
      current_timezone: "Europe/London",
    });

    await page.goto("/");
    await expectNoCrash(page);

    expect(new URL(page.url()).searchParams.get("mock")).toBeNull();
    await expect(page.getByTestId("home-feed-page")).toBeVisible();
    await expect(page.getByTestId("consumer-page-shell-content")).toHaveAttribute("data-block", "SHELL_CONTENT");
    await page.waitForTimeout(2000);
    const hasVerdict = await page.getByTestId("today-verdict").count();
    if (!hasVerdict) {
      const bodyText = await page.locator("body").innerText();
      throw new Error(`Real-backend signed Today did not render canonical surface. Body: ${bodyText}`);
    }
    await page.waitForLoadState("networkidle");
    await expect(page.getByTestId("today-score-energy")).toBeVisible();
    await expect(page.getByTestId("today-score-money")).toBeVisible();
    await expect(page.getByTestId("today-score-love")).toBeVisible();
    await expect(page.getByTestId("today-score-focus")).toBeVisible();
    await expect(page.getByTestId("today-cta-panel")).toBeVisible();
    await expect(page.getByTestId("today-cta-week")).toBeVisible();
    await expect(page.getByTestId("today-cta-premium")).toBeVisible();
    await expect(page.getByTestId("today-score-energy")).toContainText("Тонус");
    await expect(page.getByTestId("today-score-money")).toContainText("Работа и деньги");
    await expect(page.getByTestId("today-score-love")).toContainText("Чувства");
    await expect(page.getByTestId("today-score-focus")).toContainText("Фокус");
    await expect(page.getByTestId("today-render-path")).toHaveAttribute("data-render-path", "canonical");
    await expect(page.locator('[data-testid="today-windows"]')).toHaveCount(0);
    await expect(page.locator('[data-testid="today-actions"]')).toHaveCount(0);
    await expect(page.locator('[data-testid="today-risks"]')).toHaveCount(0);
    await expect(page.locator('[data-testid="today-explainability"]')).toHaveCount(0);

    await expect.poll(() => profileHeaders.at(-1)).toBe(runtime.initData);
    await expect.poll(() => feedHeaders.at(-1)).toBe(runtime.initData);

    await expectNoRouteHygieneIssues("/", hygiene);
    hygiene.dispose();
  });


  test("renders signed Today no-data state from canonical payload without complete domains", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);
    const runtime = await bootstrapSignedTelegram(page, {
      user: {
        id: 45454546,
        first_name: "Signed",
        last_name: "NoData",
        username: "signed_nodata",
        language_code: "ru",
      },
    });

    const profileHeaders: string[] = [];
    const feedHeaders: string[] = [];

    await mockCommonApis(page);

    await page.route("**/api/users/me", async (route) => {
      profileHeaders.push(route.request().headers()["x-telegram-auth"] ?? "");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ...canonicalTodayProfile,
          full_name: "Signed NoData",
          telegram_id: 45454546,
        }),
      });
    });

    await page.route("**/api/feed/today", async (route) => {
      feedHeaders.push(route.request().headers()["x-telegram-auth"] ?? "");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          day_brief: {
            version: "day_brief_canon_v1",
            status: "partial",
            date: "2026-04-10",
            personalization_level: "personalized_v2",
            hero: {
              title: "День пока не собран полностью",
              subtitle: "Нет ни одной готовой сферы для честного дневного вывода.",
              day_type: "balance",
            },
            domains: {
              energy: { key: "energy", title: "Тонус", score_status: "missing", score: null, status: null, description_status: "missing", description: null, why_status: "missing", why_astro_text: null, evidence_refs: [] },
              money: { key: "money", title: "Работа и деньги", score_status: "missing", score: null, status: null, description_status: "missing", description: null, why_status: "missing", why_astro_text: null, evidence_refs: [] },
              love: { key: "love", title: "Чувства", score_status: "missing", score: null, status: null, description_status: "missing", description: null, why_status: "missing", why_astro_text: null, evidence_refs: [] },
              focus: { key: "focus", title: "Фокус", score_status: "missing", score: null, status: null, description_status: "missing", description: null, why_status: "missing", why_astro_text: null, evidence_refs: [] },
            },
          },
        }),
      });
    });

    await page.goto("/");
    await expectNoCrash(page);
    await expect(page.getByTestId("today-no-data-state")).toBeVisible();
    await expect(page.getByTestId("today-render-path")).toHaveAttribute("data-render-path", "no_data");
    await expect(page.getByText("Нет данных на сегодня")).toBeVisible();
    await expect.poll(() => profileHeaders[0]).toBe(runtime.initData);
    await expect.poll(() => feedHeaders[0]).toBe(runtime.initData);
    await expectNoRouteHygieneIssues("/", hygiene);
    hygiene.dispose();
  });

  test("renders signed Today error state for failed canonical payload", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);
    const runtime = await bootstrapSignedTelegram(page, {
      user: {
        id: 45454547,
        first_name: "Signed",
        last_name: "Error",
        username: "signed_error",
        language_code: "ru",
      },
    });

    const feedHeaders: string[] = [];

    await mockCommonApis(page);

    await page.route("**/api/users/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ...canonicalTodayProfile,
          full_name: "Signed Error",
          telegram_id: 45454547,
        }),
      });
    });

    await page.route("**/api/feed/today", async (route) => {
      feedHeaders.push(route.request().headers()["x-telegram-auth"] ?? "");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          day_brief: {
            version: "day_brief_canon_v1",
            status: "failed",
            date: "2026-04-10",
            personalization_level: "personalized_v2",
            hero: { title: "Расчёт дня не завершён", subtitle: "Канонический слой вернул ошибку без подмены.", day_type: "balance" },
            domains: {
              energy: { key: "energy", title: "Тонус", score_status: "failed", score: null, status: null, description_status: "failed", description: null, why_status: "failed", why_astro_text: null, evidence_refs: [] },
              money: { key: "money", title: "Работа и деньги", score_status: "failed", score: null, status: null, description_status: "failed", description: null, why_status: "failed", why_astro_text: null, evidence_refs: [] },
              love: { key: "love", title: "Чувства", score_status: "failed", score: null, status: null, description_status: "failed", description: null, why_status: "failed", why_astro_text: null, evidence_refs: [] },
              focus: { key: "focus", title: "Фокус", score_status: "failed", score: null, status: null, description_status: "failed", description: null, why_status: "failed", why_astro_text: null, evidence_refs: [] },
            },
          },
        }),
      });
    });

    await page.goto("/");
    await expectNoCrash(page);
    await expect(page.getByTestId("today-error-state")).toBeVisible();
    await expect(page.getByTestId("today-render-path")).toHaveAttribute("data-render-path", "error");
    await expect(page.getByText(/Расчёт дня не завершён|Не удалось собрать дневной слой/i)).toBeVisible();
    await expect.poll(() => feedHeaders[0]).toBe(runtime.initData);
    await expectNoRouteHygieneIssues("/", hygiene);
    hygiene.dispose();
  });

  test("renders signed Today partial-ready with honest domain_failed state", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);
    const runtime = await bootstrapSignedTelegram(page, {
      user: {
        id: 45454548,
        first_name: "Signed",
        last_name: "Partial",
        username: "signed_partial",
        language_code: "ru",
      },
    });

    const feedHeaders: string[] = [];

    await mockCommonApis(page);

    await page.route("**/api/users/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ...canonicalTodayProfile,
          full_name: "Signed Partial",
          telegram_id: 45454548,
        }),
      });
    });

    await page.route("**/api/feed/today", async (route) => {
      feedHeaders.push(route.request().headers()["x-telegram-auth"] ?? "");
      const feed = JSON.parse(JSON.stringify(canonicalTodayFeed));
      feed.day_brief.status = "partial";
      feed.day_brief.domains.money = {
        key: "money",
        title: "Работа и деньги",
        score_status: "failed",
        score: null,
        status: null,
        description_status: "failed",
        description: null,
        why_status: "failed",
        why_astro_text: null,
        evidence_refs: [],
      };
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(feed) });
    });

    await page.goto("/");
    await expectNoCrash(page);
    await expect(page.getByTestId("today-verdict")).toBeVisible();
    await expect(page.getByTestId("today-render-path")).toHaveAttribute("data-render-path", "canonical");
    await expect(page.getByTestId("today-score-money")).toContainText("Ошибка");
    await expect(page.getByTestId("today-score-money")).toContainText("Ошибка расчёта этой сферы.");
    await expect(page.getByTestId("today-score-energy")).toContainText("Тонус");
    await expect.poll(() => feedHeaders[0]).toBe(runtime.initData);
    await expectNoRouteHygieneIssues("/", hygiene);
    hygiene.dispose();
  });

  test("loads profile via real signed X-Telegram-Auth header", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);
    const runtime = await bootstrapSignedTelegram(page, {
      user: {
        id: 42424242,
        first_name: "Signed",
        last_name: "Profile",
        username: "signed_profile",
        language_code: "ru",
      },
    });

    const seenHeaders: string[] = [];
    await page.route("**/api/users/me", async (route) => {
      seenHeaders.push(route.request().headers()["x-telegram-auth"] ?? "");
      await route.continue();
    });

    await page.goto("/profile");
    await expectNoCrash(page);

    await expect(page.getByText("Signed Profile")).toBeVisible();
    await expect(page.getByText("ID: 42424242")).toBeVisible();
    await expect.poll(() => seenHeaders[0]).toBe(runtime.initData);

    await expectNoRouteHygieneIssues("/profile", hygiene);
    hygiene.dispose();
  });

  test("loads and saves profile edit via real signed X-Telegram-Auth header", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);
    const runtime = await bootstrapSignedTelegram(page, {
      user: {
        id: 41414141,
        first_name: "Signed",
        last_name: "Editor",
        username: "signed_editor",
        language_code: "ru",
      },
    });

    const requests: Array<{ method: string; auth: string; body: string | null }> = [];
    let savedProfile = {
      full_name: "Signed Editor",
      birth_date: "1990-05-20",
      birth_time: "08:45",
      birth_time_known: true,
      birth_place: "Moscow, Russia",
      birth_lat: 55.7558,
      birth_lon: 37.6173,
      birth_timezone: "Europe/Moscow",
      sun_sign: "Taurus",
      telegram_id: 41414141,
      days_left: 14,
      is_partner: false,
      referral_code: "SIGNED42",
      subscription_active_until: "2026-05-01T00:00:00.000Z",
    };

    await page.route("**/api/geo/autocomplete?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: "spb",
            name: "Saint Petersburg",
            admin1: "Saint Petersburg",
            country: "Russia",
            lat: 59.9343,
            lon: 30.3351,
            label: "Saint Petersburg, Russia",
          },
        ]),
      });
    });

    await page.route("**/api/geo/timezone?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ timezone_id: "Europe/Moscow" }),
      });
    });

    await page.route("**/api/users/me", async (route) => {
      const request = route.request();
      requests.push({
        method: request.method(),
        auth: request.headers()["x-telegram-auth"] ?? "",
        body: request.postData() ?? null,
      });

      if (request.method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(savedProfile),
        });
        return;
      }

      if (request.method() === "PUT") {
        const payload = JSON.parse(request.postData() ?? "{}");
        savedProfile = {
          ...savedProfile,
          ...payload,
          birth_date: payload.birth_date ?? savedProfile.birth_date,
          birth_time: payload.birth_time ?? savedProfile.birth_time,
          birth_time_known: payload.birth_time_known ?? savedProfile.birth_time_known,
          birth_place: payload.birth_place ?? savedProfile.birth_place,
          birth_lat: payload.birth_lat ?? savedProfile.birth_lat,
          birth_lon: payload.birth_lon ?? savedProfile.birth_lon,
          birth_timezone: payload.birth_timezone ?? savedProfile.birth_timezone,
          sun_sign: payload.sun_sign ?? savedProfile.sun_sign,
        };

        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ ok: true }),
        });
        return;
      }

      await route.continue();
    });

    await page.goto("/profile/edit");
    await expectNoCrash(page);

    await expect(page.getByRole("heading", { name: "Настройки профиля" })).toBeVisible();
    await expect.poll(() => requests.find((entry) => entry.method === "GET")?.auth ?? "").toBe(runtime.initData);

    const nameInput = page.locator('label:has-text("Имя") + input');
    const placeInput = page.getByPlaceholder("Начните вводить город...");
    const saveButton = page.getByRole("button", { name: "Сохранить изменения" });

    await expect(nameInput).toHaveValue("Signed Editor");
    await nameInput.fill("Signed Editor Updated");
    await placeInput.fill("Saint Petersburg");
    await page.getByRole("button", { name: /Saint Petersburg/i }).click();
    await expect(placeInput).toHaveValue(/Saint Petersburg/i);

    const saveRequest = page.waitForRequest((request) => request.url().includes("/api/users/me") && request.method() === "PUT");
    await saveButton.click({ force: true });
    await saveRequest;

    await expect.poll(() => requests.filter((entry) => entry.method === "PUT").length).toBe(1);
    const putRequest = requests.find((entry) => entry.method === "PUT");
    expect(putRequest?.auth).toBe(runtime.initData);
    expect(JSON.parse(putRequest?.body ?? "{}").full_name).toBe("Signed Editor Updated");

    await expect(page).toHaveURL(/\/profile$/);
    await expect(page.getByText("Signed Editor Updated")).toBeVisible();

    await expectNoRouteHygieneIssues("/profile/edit", hygiene);
    hygiene.dispose();
  });

  test("submits onboarding profile with signed auth header", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);
    const runtime = await bootstrapSignedTelegram(page, {
      user: {
        id: 43434343,
        first_name: "Flow",
        last_name: "Signed",
        username: "signed_flow",
        language_code: "ru",
      },
    });

    const requests: Array<{ method: string; auth: string; body: string | null }> = [];

    await page.route("**/api/geo/autocomplete?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: "msk",
            name: "Moscow",
            admin1: "Moscow",
            country: "Russia",
            lat: 55.7558,
            lon: 37.6176,
            label: "Moscow, Russia",
          },
        ]),
      });
    });

    await page.route("**/api/geo/timezone?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ timezone_id: "Europe/Moscow" }),
      });
    });

    await page.route("**/api/users/me", async (route) => {
      const request = route.request();
      requests.push({
        method: request.method(),
        auth: request.headers()["x-telegram-auth"] ?? "",
        body: request.postData() ?? null,
      });
      await route.continue();
    });

    await page.goto("/onboarding/profile");
    await expectNoCrash(page);

    await page.getByRole("button", { name: "Начать путешествие" }).click();
    await page.getByPlaceholder("Ваше имя").fill("Signed Flow");
    await page.locator('input[type="date"]').fill("1991-08-21");
    await page.getByRole("button", { name: "Далее" }).click();
    await page.locator('input[type="time"]').fill("08:45");
    await page.getByRole("button", { name: "Далее" }).click();
    const cityInput = page.getByPlaceholder("Начните вводить город...");
    await cityInput.fill("Moscow");
    await page.getByRole("button", { name: /Moscow, Russia/i }).click();
    await page.getByRole("button", { name: "Рассчитать карту" }).click();

    await expect.poll(() => requests.filter((entry) => entry.method === "PUT").length).toBe(1);
    const putRequest = requests.find((entry) => entry.method === "PUT");
    expect(putRequest?.auth).toBe(runtime.initData);
    expect(JSON.parse(putRequest?.body ?? "{}").full_name).toBe("Signed Flow");

    await expectNoRouteHygieneIssues("/onboarding/profile", hygiene);
    hygiene.dispose();
  });

  test("loads week authenticated content via signed auth without mock mode", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);
    const runtime = await bootstrapSignedTelegram(page, {
      user: {
        id: 44444444,
        first_name: "Week",
        last_name: "Signed",
        username: "signed_week",
        language_code: "ru",
      },
    });

    const reportId = "signed-week-report";
    const reportListHeaders: string[] = [];
    const reportDetailHeaders: string[] = [];

    await page.route("**/api/reports/my?**", async (route) => {
      reportListHeaders.push(route.request().headers()["x-telegram-auth"] ?? "");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: reportId,
            report_type: "week_forecast",
            status: "completed",
          },
        ]),
      });
    });

    await page.route(`**/api/reports/${reportId}`, async (route) => {
      reportDetailHeaders.push(route.request().headers()["x-telegram-auth"] ?? "");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          report: {
            id: reportId,
            report_type: "week_forecast",
            status: "completed",
          },
          week_brief: {
            version: "week_brief_v1",
            week_start: "2026-03-30",
            week_end: "2026-04-05",
            personalization_level: "full",
            fallback_mode: false,
            status: "ready",
            summary: {
              headline: "Неделя собрана для авторизованного пользователя",
              subhead: "Signed auth lane доходит до персонализированного week surface без mock runtime.",
              week_type: "balance",
              theme: "Проверка signed auth content path",
            },
            day_cards: [
              { date: "2026-03-30", weekday: "mon", mode: "green", score: 82, headline: "Подтвердите приоритет", best_for: ["План"], avoid: ["Шум"] },
              { date: "2026-03-31", weekday: "tue", mode: "yellow", score: 64, headline: "Уточните стыки", best_for: ["Уточнения"], avoid: ["Спешка"] },
              { date: "2026-04-01", weekday: "wed", mode: "green", score: 78, headline: "Фиксируйте результат", best_for: ["Сборка"], avoid: ["Рывок"] },
              { date: "2026-04-02", weekday: "thu", mode: "yellow", score: 58, headline: "Держите темп", best_for: ["Редактура"], avoid: ["Конфликт"] },
              { date: "2026-04-03", weekday: "fri", mode: "green", score: 80, headline: "Закрепите договорённости", best_for: ["Итоги"], avoid: ["Перегруз"] },
              { date: "2026-04-04", weekday: "sat", mode: "yellow", score: 55, headline: "Ослабьте давление", best_for: ["Быт"], avoid: ["Суета"] },
              { date: "2026-04-05", weekday: "sun", mode: "green", score: 76, headline: "Соберите следующую неделю", best_for: ["План"], avoid: ["Рывок"] },
            ],
            domains: [
              { key: "work_money", title: "Работа и деньги", status: "green", value: 79, headline: "Главный сигнал недели", advice: "Фиксируйте результат письменно." },
              { key: "relationships", title: "Отношения", status: "yellow", value: 61, headline: "Нужны уточнения", advice: "Сверяйте ожидания заранее." },
              { key: "energy", title: "Энергия", status: "yellow", value: 57, headline: "Берегите ресурс", advice: "Оставляйте буфер между задачами." },
            ],
            best_uses: [
              { id: "a1", text: "Двигайте один главный приоритет за раз." },
              { id: "a2", text: "Возвращайтесь ко второму проходу без давления." },
            ],
            risks: [
              { id: "r1", text: "Не распыляйтесь на параллельные обещания." },
            ],
            major_factors: [
              { id: "f1", label: "Auth lane", impact: "high", explanation_human: "Контент приходит по real signed runtime и персональному report path." },
            ],
            deep_sections: [
              {
                id: "strategy",
                slug: "week_strategy",
                title: "Стратегия недели",
                summary: "Signed auth прошёл до content surface.",
                body_markdown: "# Стратегия недели\n\nКонтент загружен через signed Telegram runtime без mock mode.",
                is_primary: true,
                order: 0,
              },
            ],
            explainability: { confidence: 0.84, birth_time_used: true, factor_count: 3, top_signal_source: "transit_natal" },
            cta: { primary: { type: "custom", label: "Открыть полный отчёт", href: `/read/${reportId}` } },
            report_ref: { report_id: reportId, report_type: "week_forecast", source_status: "completed" },
          },
          chunks: [
            {
              id: "week-strategy",
              section: "week_strategy",
              title: "Стратегия недели",
              content: "Контент загружен через signed Telegram runtime без mock mode.",
            },
          ],
        }),
      });
    });

    await page.goto("/week");
    await expectNoCrash(page);

    await expect(page.getByTestId("week-map-surface")).toBeVisible();
    await expect(page.getByTestId("week-map-surface")).toContainText("Неделя собрана для авторизованного пользователя");
    await expect(page.getByTestId("week-domain-panel")).toContainText("Работа и деньги");
    await expect(page.getByTestId("week-deep-sections")).toContainText("Контент загружен через signed Telegram runtime без mock mode.");
    await expect(page.getByTestId("week-primary-cta")).toHaveAttribute("href", `/read/${reportId}`);

    await expect.poll(() => reportListHeaders[0]).toBe(runtime.initData);
    await expect.poll(() => reportDetailHeaders[0]).toBe(runtime.initData);

    await expectNoRouteHygieneIssues("/week", hygiene);
    hygiene.dispose();
  });
});
