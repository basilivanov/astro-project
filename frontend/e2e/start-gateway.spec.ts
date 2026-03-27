import { test, expect, type Page, type Route } from "@playwright/test";

import { bootstrapMockTelegram, expectNoCrash } from "./utils";

type TelemetryEvent = {
  event: string;
  payload: Record<string, unknown>;
};

async function installTelemetryCapture(page: Page, telemetry: TelemetryEvent[]) {
  await page.route("**/api/analytics/**", async (route: Route) => {
    const request = route.request();
    const bodyText = request.postData() ?? "";

    try {
      const parsed = JSON.parse(bodyText);
      const batch = Array.isArray(parsed?.events) ? parsed.events : parsed ? [parsed] : [];
      for (const item of batch) {
        telemetry.push({
          event: typeof item?.event === "string" ? item.event : typeof item?.event_name === "string" ? item.event_name : "unknown",
          payload: (item ?? {}) as Record<string, unknown>,
        });
      }
    } catch {}

    await route.fulfill({ status: 204, body: "" });
  });
}

async function waitForTelemetry(telemetry: TelemetryEvent[], eventName: string) {
  await expect
    .poll(() => telemetry.some((item) => item.event === eventName), { timeout: 15000 })
    .toBe(true);
  return telemetry;
}

test.describe("VM-START-GATEWAY", () => {
  test("redirects mock sessions into feed with START_GATE telemetry", async ({ page }) => {
    const telemetry: TelemetryEvent[] = [];
    await installTelemetryCapture(page, telemetry);
    await bootstrapMockTelegram(page);

    await page.goto("/start?flow=FLOW-HOME-FEED");
    await page.waitForURL((url) => url.pathname === "/" && url.searchParams.get("mock") === "1", { timeout: 15000 });
    await expectNoCrash(page);
    await expect(page.getByTestId("home-feed-page")).toBeVisible();

    await waitForTelemetry(telemetry, "start.redirect_decision");
    const redirectEvent = telemetry.find((item) => item.event === "start.redirect_decision");
    const payload = redirectEvent?.payload ?? {};

    expect(payload.flow_id).toBe("FLOW-HOME-FEED");
    expect(payload.block).toBe("START_GATE");
    expect(payload.semantic_block).toBe("START_GATE");
    expect(payload.target_path).toBe("/?mock=1");
    expect(payload.decision).toBe("mock_feed");
    expect(payload.event_name).toBe("start.redirect_decision");
  });

  test("shows auth wait gate for guest mode with AUTH_WAIT telemetry", async ({ page }) => {
    const telemetry: TelemetryEvent[] = [];
    await installTelemetryCapture(page, telemetry);
    await bootstrapMockTelegram(page, { guest: true });

    await page.goto("/start?guest=1&flow=FLOW-HOME-FEED");
    await page.waitForURL((url) => url.pathname === "/start" && url.searchParams.get("guest") === "1", { timeout: 15000 });
    await expectNoCrash(page);
    await expect(page.getByTestId("start-auth-gate")).toBeVisible();
    await expect(page.getByTestId("start-auth-gate-cta")).toBeVisible();
    await expect(page.getByTestId("start-auth-gate-hint")).toBeVisible();

    await waitForTelemetry(telemetry, "start.auth_wait");
    const authWaitEvent = telemetry.find((item) => item.event === "start.auth_wait");
    const payload = authWaitEvent?.payload ?? {};

    expect(payload.flow_id).toBe("FLOW-HOME-FEED");
    expect(payload.block).toBe("AUTH_WAIT");
    expect(payload.semantic_block).toBe("AUTH_WAIT");
    expect(payload.telegram_mode).toBe("guest");
    expect(payload.telegram_ready).toBe(true);
    expect(payload.decision).toBe("show_auth_wait");
    expect(payload.event_name).toBe("start.auth_wait");
  });

  test("routes telegram profile completion into onboarding with PROFILE_ROUTE telemetry", async ({ page }) => {
    const telemetry: TelemetryEvent[] = [];
    await installTelemetryCapture(page, telemetry);

    await page.addInitScript(() => {
      window.sessionStorage.removeItem("mock_telegram_user");
      (window as Window & typeof globalThis & { __TEST_TELEGRAM_RUNTIME__?: unknown }).__TEST_TELEGRAM_RUNTIME__ = {
        initData: "telegram-auth-123",
        user: { id: 777, first_name: "Auth", last_name: "User" },
      };
    });

    await page.route("**/api/users/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          full_name: "Debug User",
          birth_date: "",
          birth_time: "",
          birth_time_known: false,
        }),
      });
    });

    await page.goto("/start?flow=FLOW-HOME-FEED");
    await expect
      .poll(() => telemetry.map((item) => item.event), { timeout: 15000 })
      .toContain("start.profile_check_started");
    await expect
      .poll(() => telemetry.some((item) => item.event === "start.profile_redirect"), { timeout: 15000 })
      .toBe(true);

    const startEvent = telemetry.find((item) => item.event === "start.profile_check_started");
    const redirectEvent = telemetry.find((item) => item.event === "start.profile_redirect");
    const startPayload = startEvent?.payload ?? {};
    const redirectPayload = redirectEvent?.payload ?? {};

    expect(startPayload.flow_id).toBe("FLOW-HOME-FEED");
    expect(startPayload.block).toBe("PROFILE_ROUTE");
    expect(startPayload.target_path).toBe("/api/users/me");
    expect(startPayload.event_name).toBe("start.profile_check_started");

    expect(redirectPayload.flow_id).toBe("FLOW-HOME-FEED");
    expect(redirectPayload.block).toBe("PROFILE_ROUTE");
    expect(redirectPayload.target_path).toBe("/onboarding/profile");
    expect(redirectPayload.decision).toBe("profile_onboarding");
    expect(redirectPayload.profile_complete).toBe(false);
    expect(redirectPayload.event_name).toBe("start.profile_redirect");
  });
});
