import { expect, test } from "@playwright/test";

import { bootstrapSignedTelegram, bootstrapTelegramWebApp } from "./utils";

const HARNESS_URL = "/__telegram_harness__";
const HARNESS_HTML = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>telegram-harness</title></head><body><div id="app">telegram harness</div></body></html>`;

async function openHarnessDocument(page: Parameters<typeof test>[0]["page"]) {
  await page.route(HARNESS_URL, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/html",
      body: HARNESS_HTML,
    });
  });

  await page.goto(HARNESS_URL);
}

test.describe("Telegram WebApp harness", () => {
  test("injects reusable runtime before page bootstrap", async ({ page }) => {
    await bootstrapTelegramWebApp(page, {
      initData: "test-init-data",
      platform: "ios",
      colorScheme: "dark",
      viewportHeight: 912,
      viewportStableHeight: 860,
      initDataUnsafe: {
        user: {
          id: 777,
          first_name: "Harness",
          last_name: "Verifier",
          username: "harness_verifier",
          language_code: "en",
        },
      },
    });

    await openHarnessDocument(page);

    const snapshot = await page.evaluate(() => {
      const webApp = (window as Window & typeof globalThis & { Telegram?: { WebApp?: any } }).Telegram?.WebApp;
      webApp?.expand?.();
      webApp?.MainButton?.setText?.("Continue");
      webApp?.MainButton?.show?.();
      webApp?.BackButton?.show?.();

      return {
        initData: webApp?.initData,
        userId: webApp?.initDataUnsafe?.user?.id,
        platform: webApp?.platform,
        colorScheme: webApp?.colorScheme,
        viewportHeight: webApp?.viewportHeight,
        viewportStableHeight: webApp?.viewportStableHeight,
        isExpanded: webApp?.isExpanded,
        mainButtonText: webApp?.MainButton?.text,
        mainButtonVisible: webApp?.MainButton?.isVisible,
        backButtonVisible: webApp?.BackButton?.isVisible,
        testRuntime: (window as Window & typeof globalThis & { __TEST_TELEGRAM_RUNTIME__?: any }).__TEST_TELEGRAM_RUNTIME__,
      };
    });

    expect(snapshot).toMatchObject({
      initData: "test-init-data",
      userId: 777,
      platform: "ios",
      colorScheme: "dark",
      viewportHeight: 912,
      viewportStableHeight: 860,
      isExpanded: true,
      mainButtonText: "Continue",
      mainButtonVisible: true,
      backButtonVisible: true,
      testRuntime: {
        initData: "test-init-data",
        user: {
          id: 777,
        },
      },
    });
  });

  test("preserves signed auth lane semantics", async ({ page }) => {
    const runtime = await bootstrapSignedTelegram(page, {
      user: {
        id: 4242,
        first_name: "Signed",
        last_name: "Harness",
        username: "signed_harness",
        language_code: "ru",
      },
      authDate: 1_712_345_678,
    });

    await openHarnessDocument(page);

    const snapshot = await page.evaluate(() => ({
      sessionMockUser: window.sessionStorage.getItem("mock_telegram_user"),
      initData: (window as Window & typeof globalThis & { Telegram?: { WebApp?: any } }).Telegram?.WebApp?.initData,
      userId: (window as Window & typeof globalThis & { Telegram?: { WebApp?: any } }).Telegram?.WebApp?.initDataUnsafe?.user?.id,
      runtime: (window as Window & typeof globalThis & { __TEST_TELEGRAM_RUNTIME__?: any }).__TEST_TELEGRAM_RUNTIME__,
    }));

    expect(snapshot.sessionMockUser).toBeNull();
    expect(snapshot.initData).toBe(runtime.initData);
    expect(snapshot.userId).toBe(4242);
    expect(snapshot.runtime).toMatchObject({
      initData: runtime.initData,
      user: {
        id: 4242,
      },
    });
  });
});
