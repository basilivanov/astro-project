import { expect, test } from "@playwright/test";
import { attachRuntimeErrorGuards, bootstrapMockTelegram, bootstrapSignedTelegram, expectNoCrash, expectNoRuntimeErrors } from "./utils";
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

async function seedSignedTodayProfile(page: Parameters<typeof test>[0]["page"], initData: string, fullName: string) {
  const response = await page.request.put('/api/users/me', {
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Auth': initData,
    },
    data: {
      full_name: fullName,
      birth_date: '1991-08-21',
      birth_time: '08:45',
      birth_time_known: true,
      birth_place: 'Moscow, Russia',
      birth_lat: 55.7558,
      birth_lon: 37.6176,
      birth_timezone: 'Europe/Moscow',
      current_timezone: 'Europe/Moscow',
    },
  });

  expect(response.ok()).toBeTruthy();
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
    await expect(page.getByTestId("today-windows")).toContainText("Рабочий импульс");
    await expect(page.getByTestId("today-windows")).toContainText("Закройте главную задачу до обеда.");
    await expect(page.getByTestId("today-actions")).toContainText("Закрыть один глубокий рабочий блок");
    await expect(page.getByTestId("today-risks")).toContainText("Не разгоняйте разговоры в конфликтный тон");
    await expect(page.getByTestId("today-explainability")).toContainText("Почему такой день");
    await expect(page.getByTestId("home-feed-page")).not.toContainText(/объяснение недоступно/i);
    await expect(page.getByTestId("today-cta-week")).toContainText("Открыть неделю");
    await expect(page.getByTestId("today-cta-premium")).toContainText("История разборов");
    await expect(page.getByTestId("home-feed-page")).not.toContainText(/\bsignal_only\b/i);
    await expect(page.getByTestId("home-feed-page")).not.toContainText(/\bstructured_value\b/i);
    await expect(page.getByTestId("home-feed-page")).not.toContainText(/\bgreen\b/i);
    await expect(page.getByTestId("home-feed-page")).not.toContainText(/светофор\s+money\s*:\s*green/i);
    await expect(page.getByTestId("home-feed-page")).not.toContainText(/\ball_week\b/i);
    await expectNoRuntimeErrors(hygiene, "today canonical persona render");
    hygiene.dispose();
  });

  test("score disclosure stays non-empty when canonical persona has no scoped aspects", async ({ page }) => {
    await bootstrapTelegramMobile(page);
    await page.goto("/");

    const scoreCard = page.getByTestId("today-score-energy");
    await expect(scoreCard).toContainText("72");
    await scoreCard.getByRole("button", { name: /Энергия: 72/ }).click();

    const disclosure = scoreCard.getByTestId("today-score-details-energy");
    await expect(disclosure).toBeVisible();
    await expect(disclosure).toContainText("Что повлияло");
    await expect(disclosure).not.toContainText(/объяснение недоступно/i);
  });

  test("score disclosure stays honest when why_text is reused across domains", async ({ page }) => {
    await bootstrapTelegramMobile(page, {
      feedState: "ready",
      profileOverride: canonicalPersona.profile,
      feedOverride: {
        ...canonicalPersona.feed,
        day_brief: {
          ...canonicalPersona.feed.day_brief,
          scores: [
            {
              key: "money",
              title: "Работа и деньги",
              value: 58,
              status: "yellow",
              advice: "Сначала сверяйте цифры и сроки.",
              details: {
                why_title: "Почему сфера такая",
                why_text: "Двигай одну покупку или решение за раз: импульсивные траты и эмоциональные обещания сегодня дают лишний шум.",
                supporting_factors: [],
              },
            },
            {
              key: "love",
              title: "Чувства",
              value: 55,
              status: "yellow",
              advice: "Говорите мягче и проверяйте ожидания.",
              details: {
                why_title: "Почему сфера такая",
                why_text: "Двигай одну покупку или решение за раз: импульсивные траты и эмоциональные обещания сегодня дают лишний шум.",
                supporting_factors: [],
              },
            },
          ],
          personalized_factors: [],
          explainability: {
            ...canonicalPersona.feed.day_brief.explainability,
            selected_factors: [
              {
                id: "sf-generic-repeat",
                label: "Общий сигнал дня",
                explanation_human: "Двигай одну покупку или решение за раз: импульсивные траты и эмоциональные обещания сегодня дают лишний шум.",
                signal: 0.68,
              },
            ],
          },
        },
      },
    });

    await page.goto("/");

    const workCard = page.getByTestId("today-score-money");
    await workCard.getByRole("button", { name: /Работа и деньги: 58/ }).click();
    await expect(workCard.getByTestId("today-score-details-money")).toBeVisible();
    await expect(workCard.getByTestId("today-score-details-money")).not.toContainText(/объяснение недоступно/i);

    const relationshipsCard = page.getByTestId("today-score-love");
    await relationshipsCard.getByRole("button", { name: /Чувства: 55/ }).click();
    await expect(relationshipsCard.getByTestId("today-score-details-love")).toBeVisible();
    await expect(relationshipsCard.getByTestId("today-score-details-love")).not.toContainText(/объяснение недоступно/i);
  });

  test("real DEV payload keeps focus disclosure non-empty when only generic selected-factor echo exists", async ({ page }) => {
    test.skip(!process.env.TELEGRAM_BOT_TOKEN, "TELEGRAM_BOT_TOKEN is required for signed Telegram E2E lane");
    await page.setViewportSize({ width: 390, height: 844 });
    await bootstrapSignedTelegram(page, {
      user: {
        id: 45454545,
        first_name: "Today",
        last_name: "Signed",
        username: "signed_today",
        language_code: "ru",
      },
    });
    await page.route("**/api/feed/today", async (route) => {
      const response = await route.fetch();
      const json = await response.json();
      await route.fulfill({
        response,
        contentType: "application/json",
        body: JSON.stringify(json),
      });
    });

    await page.route("**/api/users/me", async (route) => {
      const response = await route.fetch();
      await route.fulfill({ response, body: await response.text(), contentType: "application/json" });
    });

    await page.goto("/?mock=0");

    const focusCard = page.getByTestId("today-score-focus");
    await expect(focusCard).toBeVisible();
    await focusCard.getByRole("button", { name: /Фокус:/ }).click();

    const disclosure = focusCard.getByTestId("today-score-details-focus");
    await expect(disclosure).toBeVisible();
    await expect(disclosure).not.toContainText(/объяснение недоступно/i);
  });

  test("real DEV payload keeps score disclosures honest without placeholder fallback copy", async ({ page }) => {
    test.skip(!process.env.TELEGRAM_BOT_TOKEN, "TELEGRAM_BOT_TOKEN is required for signed Telegram E2E lane");
    await page.setViewportSize({ width: 390, height: 844 });
    await bootstrapSignedTelegram(page, {
      user: {
        id: 45454546,
        first_name: "Today",
        last_name: "Scoped",
        username: "signed_today_scoped",
        language_code: "ru",
      },
    });

    await page.route("**/api/feed/today", async (route) => {
      const response = await route.fetch();
      const json = await response.json();
      await route.fulfill({ response, contentType: "application/json", body: JSON.stringify(json) });
    });

    await page.route("**/api/users/me", async (route) => {
      const response = await route.fetch();
      await route.fulfill({ response, body: await response.text(), contentType: "application/json" });
    });

    await page.goto("/?mock=0");

    for (const key of ["energy", "money", "love"] as const) {
      const card = page.getByTestId(`today-score-${key}`);
      await expect(card).toBeVisible();
      await card.locator("button").first().click();
      const disclosure = card.getByTestId(`today-score-details-${key}`);
      if (await disclosure.count()) {
        await expect(disclosure).not.toContainText("Нажмите на карточку, чтобы открыть подробный разбор этой сферы, когда он доступен в персональной сводке.");
        await expect(disclosure).not.toContainText(/\btraffic\s*light\b/i);
        await expect(disclosure).not.toContainText(/\bсветофор\b/i);
      }
    }
  });

  test("signed Telegram lane keeps score disclosures honest across user shapes", async ({ page }) => {
    test.skip(!process.env.TELEGRAM_BOT_TOKEN, "TELEGRAM_BOT_TOKEN is required for signed Telegram E2E lane");

    const signedUsers = [
      {
        id: 45454546,
        first_name: "Today",
        last_name: "Scoped",
        username: "signed_today_scoped",
        language_code: "ru",
        fullName: "Today Scoped",
      },
      {
        id: 833478509,
        first_name: "Real",
        last_name: "Lane",
        username: "real_lane",
        language_code: "ru",
        fullName: "Real Lane",
      },
      {
        id: 45454545,
        first_name: "Today",
        last_name: "Signed",
        username: "signed_today",
        language_code: "ru",
        fullName: "Today Signed",
      },
    ] as const;

    await page.setViewportSize({ width: 390, height: 844 });

    for (const signedUser of signedUsers) {
      const runtime = await bootstrapSignedTelegram(page, { user: signedUser });
      await seedSignedTodayProfile(page, runtime.initData, signedUser.fullName);
      await page.goto('/?mock=0');
      await expectNoCrash(page);

      for (const key of ["energy", "money", "love", "focus"] as const) {
        const card = page.getByTestId(`today-score-${key}`);
        await expect(card).toBeVisible();
        await card.locator('button').first().click();
        const disclosure = card.getByTestId(`today-score-details-${key}`);
        if (await disclosure.count()) {
          await expect(disclosure).toBeVisible();
          await expect(disclosure).not.toContainText(/\bsignal_only\b/i);
          await expect(disclosure).not.toContainText(/\bstructured_value\b/i);
          await expect(disclosure).not.toContainText(/\b(?:money|love|health|focus):(?:green|yellow|red)\b/i);
          await expect(disclosure).not.toContainText(/\btraffic\s*light\b/i);
          await expect(disclosure).not.toContainText(/\bсветофор\b/i);
        }
      }

      const renderedDisclosures = page.locator('[data-testid^="today-score-"] details');
      const disclosureCount = await renderedDisclosures.count();
      for (let index = 0; index < disclosureCount; index += 1) {
        const disclosure = renderedDisclosures.nth(index);
        await expect(disclosure).not.toContainText(/\bsignal_only\b/i);
        await expect(disclosure).not.toContainText(/\bstructured_value\b/i);
        await expect(disclosure).not.toContainText(/\b(?:money|love|health|focus):(?:green|yellow|red)\b/i);
        await expect(disclosure).not.toContainText(/\btraffic\s*light\b/i);
        await expect(disclosure).not.toContainText(/\bсветофор\b/i);
        await expect(disclosure).not.toContainText('Нажмите на карточку, чтобы открыть подробный разбор этой сферы');
      }
    }
  });


  test("live lane 833478509 keeps Today UI scores in parity with /api/feed/today and renders clean disclosures", async ({ page }) => {
    test.skip(!process.env.TELEGRAM_BOT_TOKEN, "TELEGRAM_BOT_TOKEN is required for signed Telegram E2E lane");

    const signedUser = {
      id: 833478509,
      first_name: "Real",
      last_name: "Lane",
      username: "real_lane",
      language_code: "ru",
    } as const;

    await page.setViewportSize({ width: 390, height: 844 });
    const runtime = await bootstrapSignedTelegram(page, { user: signedUser });

    const apiResponse = await page.request.get('/api/feed/today', {
      headers: { 'X-Telegram-Auth': runtime.initData },
    });
    expect(apiResponse.ok()).toBeTruthy();
    const apiPayload = await apiResponse.json();
    const apiScores = new Map((apiPayload?.day_brief?.scores ?? []).map((item: any) => [item.key, item]));

    await page.goto('/?mock=0');
    await expectNoCrash(page);

    for (const key of ['energy', 'money', 'love', 'focus'] as const) {
      const expected = apiScores.get(key);
      expect(expected).toBeTruthy();
      const card = page.getByTestId(`today-score-${key}`);
      await expect(card).toBeVisible();
      await expect(card).toContainText(String(expected.value));
      await expect(card).toContainText(String(expected.advice));

      await card.locator('button').first().click();
      const disclosure = card.getByTestId(`today-score-details-${key}`);
      if (await disclosure.count()) {
        await expect(disclosure).toBeVisible();
        await expect(disclosure).not.toContainText(/\bsignal_only\b/i);
        await expect(disclosure).not.toContainText(/\bstructured_value\b/i);
        await expect(disclosure).not.toContainText(/\b(?:money|love|health|focus):(?:green|yellow|red)\b/i);
        await expect(disclosure).not.toContainText(/\btraffic\s*light\b/i);
        await expect(disclosure).not.toContainText(/\bсветофор\b/i);
      }
    }

    const moneyDisclosure = page.getByTestId('today-score-money').getByTestId('today-score-details-money');
    const loveDisclosure = page.getByTestId('today-score-love').getByTestId('today-score-details-love');
    if (await moneyDisclosure.count()) await expect(moneyDisclosure).not.toContainText('Рабочий контекст');
    if (await loveDisclosure.count()) await expect(loveDisclosure).not.toContainText('Контакт и тон');
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
