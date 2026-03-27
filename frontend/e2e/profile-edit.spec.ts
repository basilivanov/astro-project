import { test, expect } from "@playwright/test";

import { bootstrapMockTelegram, expectNoCrash } from "./utils";

test.describe("Profile edit form", () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page);
  });

  test("loads profile form, toggles fields, saves, and records clean logs", async ({ page }) => {
    const logs: string[] = [];
    const requests: Array<{ method: string; url: string; body: string | null }> = [];

    page.on("console", (msg) => {
      if (msg.type() === "error" || msg.type() === "warning") {
        logs.push(`[console:${msg.type()}] ${msg.text()}`);
      }
    });

    page.on("pageerror", (error) => {
      logs.push(`[pageerror] ${error.message}`);
    });

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

      if (request.method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            full_name: "Debug User",
            birth_date: "1990-05-20",
            birth_time: "08:45",
            birth_time_known: true,
            birth_place: "Moscow, Russia",
            birth_lat: 55.7558,
            birth_lon: 37.6173,
            birth_timezone: "Europe/Moscow",
            sun_sign: "Taurus",
          }),
        });
        return;
      }

      if (request.method() === "PUT") {
        requests.push({
          method: request.method(),
          url: request.url(),
          body: request.postData() ?? null,
        });

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
    const nameInput = page.locator('label:has-text("Имя") + input');
    const birthDateInput = page.locator('label:has-text("Дата рождения") + input');
    const birthTimeInput = page.locator('input[type="time"]');
    const zodiacSelect = page.locator('label:has-text("Знак Зодиака") + select');
    const unknownTimeCheckbox = page.getByRole("checkbox", { name: /Неизвестно/i });

    await expect(nameInput).toHaveValue("Debug User");
    await expect(birthDateInput).toHaveValue("1990-05-20");
    await expect(birthTimeInput).toHaveValue("08:45");

    await nameInput.fill("Test Consumer");
    await birthDateInput.fill("");
    await expect(zodiacSelect).toBeVisible();
    await zodiacSelect.selectOption("Gemini");
    await unknownTimeCheckbox.check();
    await expect(birthTimeInput).toHaveCount(0);

    const placeInput = page.getByPlaceholder("Начните вводить город...");
    await expect(placeInput).toBeVisible();
    await placeInput.fill("Saint Petersburg");
    await page.getByRole("button", { name: /Saint Petersburg/i }).click();
    await expect(placeInput).toHaveValue(/Saint Petersburg/i);

    const saveButton = page.getByRole("button", { name: "Сохранить изменения" });
    await expect(saveButton).toBeVisible();
    await saveButton.scrollIntoViewIfNeeded();
    const saveRequest = page.waitForRequest((request) => request.url().includes("/api/users/me") && request.method() === "PUT");
    await saveButton.click({ force: true });

    await saveRequest;
    await expect.poll(() => requests.length).toBe(1);
    await expect(page).toHaveURL(/\/profile\/edit$/);

    const payload = JSON.parse(requests[0].body ?? "{}");
    expect(payload.full_name).toBe("Test Consumer");
    expect(payload.birth_date).toBe("");
    expect(payload.birth_time_known).toBe(false);
    expect(payload.sun_sign).toBe("Gemini");
    expect(payload.birth_place).toContain("Saint Petersburg");

    test.info().attach("profile-edit-network-log", {
      body: JSON.stringify(requests, null, 2),
      contentType: "application/json",
    });
    test.info().attach("profile-edit-console-log", {
      body: logs.length ? logs.join("\n") : "no console warnings or errors",
      contentType: "text/plain",
    });
    test.info().attach("profile-edit-payload", {
      body: JSON.stringify(payload, null, 2),
      contentType: "application/json",
    });

    expect(logs, `Found console or page errors on /profile/edit: ${logs.join(", ")}`).toHaveLength(0);
  });
});
