import { expect, type Page } from "@playwright/test";

export async function bootstrapMockTelegram(page: Page, options?: {
  guest?: boolean;
  feedState?: "ready" | "fallback" | "empty" | "error";
  feedOverride?: Record<string, unknown>;
  profileOverride?: Record<string, unknown>;
}) {
  await page.addInitScript((payload) => {
    const { guest, feedState, feedOverride, profileOverride } = payload as {
      guest?: boolean;
      feedState?: "ready" | "fallback" | "empty" | "error";
      feedOverride?: Record<string, unknown>;
      profileOverride?: Record<string, unknown>;
    };

    if (guest) {
      window.sessionStorage.removeItem("mock_telegram_user");
      delete (window as Window & typeof globalThis & { Telegram?: unknown }).Telegram;
      return;
    }

    window.sessionStorage.setItem("mock_telegram_user", "1");
    (window as Window & typeof globalThis & { Telegram?: unknown; MOCK_FEED_STATE?: unknown; MOCK_FEED_OVERRIDE?: unknown; MOCK_PROFILE_OVERRIDE?: unknown }).Telegram = {
      WebApp: {
        initData: "123456789",
        ready: () => {},
        expand: () => {},
        close: () => {},
        headerColor: "#ffffff",
        backgroundColor: "#ffffff",
        initDataUnsafe: {
          user: { id: 123456789, first_name: "Debug", last_name: "User" },
        },
      },
    };

    if (feedState) {
      (window as Window & typeof globalThis & { MOCK_FEED_STATE?: unknown }).MOCK_FEED_STATE = feedState;
    }
    if (feedOverride) {
      (window as Window & typeof globalThis & { MOCK_FEED_OVERRIDE?: unknown }).MOCK_FEED_OVERRIDE = feedOverride;
    }
    if (profileOverride) {
      (window as Window & typeof globalThis & { MOCK_PROFILE_OVERRIDE?: unknown }).MOCK_PROFILE_OVERRIDE = profileOverride;
    }
  }, options ?? {});
}

export async function expectNoCrash(page: Page) {
  await expect(page.locator('body')).toBeVisible();
  await expect(page.locator('text=Application error')).toHaveCount(0);
  await expect(page.locator('text=Unhandled Runtime Error')).toHaveCount(0);
}
