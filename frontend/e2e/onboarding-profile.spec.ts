import { test, expect } from "@playwright/test";

import {
  attachConsoleAndPageErrors,
  bootstrapMockTelegram,
  expectNoCrash,
  expectNoRouteHygieneIssues,
  mockCommonApis,
} from "./utils";

test.describe("Onboarding profile P0", () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page);
    await mockCommonApis(page);
  });

  test("completes the happy path and submits onboarding profile", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);
    const requests: Array<{ method: string; url: string; body: string | null }> = [];

    await page.route("**/api/geo/autocomplete?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: "moscow",
            name: "Moscow",
            admin1: "Moscow",
            country: "Russia",
            lat: 55.7558,
            lon: 37.6173,
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
      if (request.method() === "PUT") {
        requests.push({ method: request.method(), url: request.url(), body: request.postData() ?? null });
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ ok: true }),
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true }),
      });
    });

    await page.goto("/onboarding/profile");
    await expectNoCrash(page);

    await expect(page.getByRole("button", { name: "Начать путешествие" })).toBeVisible();
    await page.getByRole("button", { name: "Начать путешествие" }).click();

    await expect(page.getByRole("heading", { name: "Давайте знакомиться" })).toBeVisible();
    await expect(page.getByPlaceholder("Ваше имя")).toHaveValue("Debug");
    await page.getByPlaceholder("Ваше имя").fill("P0 User");
    await page.locator('input[type="date"]').fill("1995-07-12");
    const detailsNextButton = page.getByRole("button", { name: "Далее" });
    await expect(detailsNextButton).toBeEnabled();
    await detailsNextButton.click();

    await expect(page.getByRole("heading", { name: "Время рождения" })).toBeVisible();
    await page.locator('input[type="time"]').fill("09:15");
    await page.getByRole("button", { name: "Далее" }).click();

    await expect(page.getByRole("heading", { name: "Место рождения" })).toBeVisible();
    const cityInput = page.getByPlaceholder("Начните вводить город...");
    await cityInput.fill("Moscow");
    await page.getByRole("button", { name: /Moscow, Russia/i }).click();
    await expect(cityInput).toHaveValue(/Moscow/i);

    const submitRequest = page.waitForRequest((request) => request.url().includes("/api/users/me") && request.method() === "PUT");
    await page.getByRole("button", { name: "Рассчитать карту" }).click();
    await submitRequest;

    await expect.poll(() => requests.length).toBe(1);
    const payload = JSON.parse(requests[0].body ?? "{}");
    expect(payload.full_name).toBe("P0 User");
    expect(payload.birth_date).toBe("1995-07-12");
    expect(payload.birth_time).toBe("09:15");
    expect(payload.birth_time_known).toBe(true);
    expect(payload.birth_place).toContain("Moscow");
    expect(payload.birth_timezone).toBe("Europe/Moscow");

    test.info().attach("onboarding-profile-payload", {
      body: JSON.stringify(payload, null, 2),
      contentType: "application/json",
    });

    await expectNoRouteHygieneIssues("/onboarding/profile", hygiene);
    hygiene.dispose();
  });

  test("keeps invalid step blocked and surfaces save failure without leaving route", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);

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
      if (request.method() === "PUT") {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ detail: "save failed" }),
        });
        return;
      }
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) });
    });

    await page.goto("/onboarding/profile");
    await expectNoCrash(page);

    const startButton = page.getByRole("button", { name: "Начать путешествие" });
    await expect(startButton).toBeEnabled();
    await startButton.click();

    await expect(page.getByRole("heading", { name: "Давайте знакомиться" })).toBeVisible();
    await page.getByPlaceholder("Ваше имя").fill("Guard User");
    await page.locator('input[type="date"]').fill("1999-09-09");
    const detailsNextButton = page.getByRole("button", { name: "Далее" });
    await expect(detailsNextButton).toBeEnabled();
    await detailsNextButton.click();

    await page.getByText("Я не знаю точное время").click();
    await page.getByRole("button", { name: "Далее" }).click();

    const cityInput = page.getByPlaceholder("Начните вводить город...");
    await cityInput.fill("Saint Petersburg");
    await page.getByRole("button", { name: /Saint Petersburg, Russia/i }).click();

    page.on("dialog", async (dialog) => {
      expect(dialog.message()).toBe("Ошибка сохранения");
      await dialog.accept();
    });

    await page.getByRole("button", { name: "Рассчитать карту" }).click();
    await expect(page).toHaveURL(/\/onboarding\/profile$/);
    expect(hygiene.logs).toEqual([
      "[console:error] Failed to load resource: the server responded with a status of 500 (Internal Server Error)",
    ]);
    hygiene.dispose();
  });
});
