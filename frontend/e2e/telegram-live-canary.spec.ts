import { expect, test } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

import {
  attachConsoleAndPageErrors,
  bootstrapTelegramWebApp,
  expectNoCrash,
} from "./utils";

type CapturedResponse = {
  status?: number;
  headers?: Record<string, string>;
  body?: unknown;
  error?: string;
  url?: string;
};

type UsersMePayload = {
  id?: unknown;
  telegram_id?: unknown;
  telegramId?: unknown;
  user?: UsersMePayload;
};

type DayDomainReadiness = {
  score_status?: unknown;
  description_status?: unknown;
  why_status?: unknown;
};

type DayBriefPayload = {
  day_brief?: {
    version?: unknown;
    status?: unknown;
    hero?: unknown;
    domains?: Record<string, DayDomainReadiness>;
  };
};

const canaryInitData = process.env.TELEGRAM_LIVE_CANARY_INIT_DATA;
const canaryUserId = process.env.TELEGRAM_LIVE_CANARY_USER_ID ?? "unknown";
const shouldRunLiveCanary = Boolean(canaryInitData && canaryUserId !== "unknown");
const liveCanaryTest = shouldRunLiveCanary ? test : test.skip;

function resolvedTelegramUserId(payload: UsersMePayload): string | null {
  const candidate = payload.telegram_id ?? payload.telegramId ?? payload.user?.telegram_id ?? payload.user?.telegramId;
  if (typeof candidate === "number" || typeof candidate === "string") return String(candidate);
  return null;
}

function summarizeDayPayload(feedPayload: DayBriefPayload) {
  const domains = feedPayload.day_brief?.domains ?? {};
  return {
    version: feedPayload.day_brief?.version ?? null,
    status: feedPayload.day_brief?.status ?? null,
    hero_present: Boolean(feedPayload.day_brief?.hero),
    domains: Object.fromEntries(Object.entries(domains).map(([key, value]) => [key, {
      score_status: value?.score_status ?? null,
      description_status: value?.description_status ?? null,
      why_status: value?.why_status ?? null,
    }])),
  };
}

function completeDomainKeys(feedPayload: DayBriefPayload) {
  return Object.entries(feedPayload.day_brief?.domains ?? {})
    .filter(([, domain]) => domain?.score_status === "complete" && domain?.description_status === "complete" && domain?.why_status === "complete")
    .map(([key]) => key);
}

async function readResponseBody(response: import("@playwright/test").Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    try {
      return await response.text();
    } catch (error) {
      return { read_error: error instanceof Error ? error.message : String(error) };
    }
  }
}

async function writeJson(filePath: string, payload: unknown) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

test.describe("telegram live canary acceptance lane", () => {
  liveCanaryTest("blocks DEV acceptance when live signed Today is no-data", async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: "flow", description: "FLOW-TODAY-CANARY-LIVE" });
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const artifactDir = path.resolve(process.cwd(), "artifacts", "day_live_canary", timestamp);
    await fs.mkdir(artifactDir, { recursive: true });

    const proofRequestId = `day-live-canary-${Date.now()}`;
    const startedAt = new Date().toISOString();
    const consoleAndPageErrors: string[] = [];
    const diagnostics: Record<string, unknown> = {
      flow_id: "FLOW-TODAY-CANARY-LIVE",
      verdict_policy: "no_data/failed/malformed/missing-trace => acceptance failure",
      request_id: proofRequestId,
      trace_id: proofRequestId,
      primary_lane: true,
      expected_user_id: canaryUserId,
      actual_user_id: null,
      started_at: startedAt,
      timestamp_window: { from: startedAt, to: null },
      users_me: {},
      feed_today: {},
      console_errors: consoleAndPageErrors,
      page_errors: consoleAndPageErrors,
      current_url: null,
      render_path: null,
      today_no_data_visible: null,
      day_payload_summary: null,
    };

    const hygiene = attachConsoleAndPageErrors(page);
    page.on("console", (message) => {
      if (message.type() === "error") consoleAndPageErrors.push(`[console:error] ${message.text()}`);
    });
    page.on("pageerror", (error) => consoleAndPageErrors.push(`[pageerror] ${error.message}`));

    await bootstrapTelegramWebApp(page, {
      initData: canaryInitData,
      initDataUnsafe: { user: { id: Number(canaryUserId) || 0, first_name: "Live", last_name: "Canary" } },
      sessionMockUser: false,
    });

    await page.route("**/api/users/me", async (route) => {
      const headers = route.request().headers();
      await route.continue({ headers: { ...headers, "X-Request-ID": proofRequestId, "X-Trace-ID": proofRequestId } });
    });
    await page.route("**/api/feed/today", async (route) => {
      const headers = route.request().headers();
      await route.continue({ headers: { ...headers, "X-Request-ID": proofRequestId, "X-Trace-ID": proofRequestId } });
    });

    page.on("response", async (response) => {
      const url = response.url();
      const method = response.request().method();
      if (method !== "GET" || (!url.includes("/api/users/me") && !url.includes("/api/feed/today"))) return;
      const key = url.includes("/api/users/me") ? "users_me" : "feed_today";
      const captured: CapturedResponse = { status: response.status(), headers: response.headers(), url, body: await readResponseBody(response) };
      diagnostics[key] = captured;
      await writeJson(path.join(artifactDir, `${key}.json`), captured);
    });

    try {
      const usersMeResponse = page.waitForResponse((response) => response.url().includes("/api/users/me") && response.request().method() === "GET");
      const feedTodayResponse = page.waitForResponse((response) => response.url().includes("/api/feed/today") && response.request().method() === "GET");

      await page.goto("/");
      await expectNoCrash(page);
      const [usersMe, feedToday] = await Promise.all([usersMeResponse, feedTodayResponse]);
      await expect(page.getByTestId("home-feed-page")).toBeVisible();
      await page.waitForLoadState("networkidle");

      const runtimeMode = await page.locator('[data-testid="home-runtime-diagnostics"]').getAttribute("data-mode").catch(() => null);
      const runtimeHasUser = await page.locator('[data-testid="home-runtime-diagnostics"]').getAttribute("data-has-user").catch(() => null);
      const runtimeHasInitData = await page.locator('[data-testid="home-runtime-diagnostics"]').getAttribute("data-has-init-data").catch(() => null);
      const runtimeInitDataLength = await page.locator('[data-testid="home-runtime-diagnostics"]').getAttribute("data-init-data-length").catch(() => null);
      const runtimeBootstrapTimedOut = await page.locator('[data-testid="home-runtime-diagnostics"]').getAttribute("data-bootstrap-timed-out").catch(() => null);

      const usersPayload = await usersMe.json() as UsersMePayload;
      const feedPayload = await feedToday.json() as DayBriefPayload;
      const actualUserId = resolvedTelegramUserId(usersPayload);
      const completeDomains = completeDomainKeys(feedPayload);
      diagnostics.current_url = page.url();
      diagnostics.runtime = { mode: runtimeMode, has_user: runtimeHasUser, has_init_data: runtimeHasInitData, init_data_length: runtimeInitDataLength, bootstrap_timed_out: runtimeBootstrapTimedOut };
      diagnostics.render_path = await page.getByTestId("today-render-path").getAttribute("data-render-path");
      diagnostics.today_no_data_visible = await page.getByTestId("today-no-data-state").isVisible().catch(() => false);
      diagnostics.actual_user_id = actualUserId;
      diagnostics.day_payload_summary = { ...summarizeDayPayload(feedPayload), complete_domain_keys: completeDomains };
      diagnostics.timestamp_window = { from: startedAt, to: new Date().toISOString() };
      diagnostics.lookup_tuple = { request_id: proofRequestId, trace_id: proofRequestId, expected_user_id: canaryUserId, actual_user_id: actualUserId, timestamp_window: diagnostics.timestamp_window };

      expect(usersMe.status(), "GET /api/users/me must be 200 for live canary").toBe(200);
      expect(feedToday.status(), "GET /api/feed/today must be 200 for live canary").toBe(200);
      expect(actualUserId, "primary live session must resolve to TELEGRAM_LIVE_CANARY_USER_ID").toBe(canaryUserId);
      expect(feedPayload?.day_brief?.version, "live canary must receive canonical Day payload").toBe("day_brief_canon_v1");
      expect(feedPayload?.day_brief?.status, "live canary Day payload must not be failed").not.toBe("failed");
      expect(feedPayload?.day_brief?.hero, "primary live Day payload must include hero").toBeTruthy();
      expect(completeDomains.length, "primary live Day payload must include at least one complete usable domain").toBeGreaterThan(0);
      expect(diagnostics.render_path, "live canary must finish on canonical render path").toBe("canonical");
      await expect(page.getByTestId("today-no-data-state")).toHaveCount(0);
      await expect(page.getByText("Нет данных на сегодня")).toHaveCount(0);
      await expect(page.getByTestId("today-verdict")).toBeVisible();
    } finally {
      diagnostics.current_url = diagnostics.current_url ?? page.url();
      diagnostics.render_path = diagnostics.render_path ?? await page.getByTestId("today-render-path").getAttribute("data-render-path").catch(() => null);
      diagnostics.today_no_data_visible = diagnostics.today_no_data_visible ?? await page.getByTestId("today-no-data-state").isVisible().catch(() => false);
      diagnostics.timestamp_window = { from: startedAt, to: new Date().toISOString() };
      diagnostics.lookup_tuple = { request_id: proofRequestId, trace_id: proofRequestId, expected_user_id: canaryUserId, actual_user_id: diagnostics.actual_user_id, timestamp_window: diagnostics.timestamp_window };
      await page.screenshot({ path: path.join(artifactDir, "screenshot.png"), fullPage: true }).catch(() => undefined);
      await writeJson(path.join(artifactDir, "diagnostics.json"), diagnostics);
      await fs.mkdir(artifactDir, { recursive: true });
      await fs.writeFile(path.join(artifactDir, "diagnostics.md"), `# Day primary live-session diagnostics\n\n- flow_id: FLOW-TODAY-CANARY-LIVE\n- primary_lane: true\n- request_id: ${proofRequestId}\n- trace_id: ${proofRequestId}\n- expected_user_id: ${canaryUserId}\n- actual_user_id: ${diagnostics.actual_user_id}\n- timestamp_window: ${JSON.stringify(diagnostics.timestamp_window)}\n- users_me_status: ${(diagnostics.users_me as CapturedResponse).status ?? "missing"}\n- feed_today_status: ${(diagnostics.feed_today as CapturedResponse).status ?? "missing"}\n- render_path: ${diagnostics.render_path}\n- today_no_data_visible: ${diagnostics.today_no_data_visible}\n- current_url: ${diagnostics.current_url}\n- runtime: ${JSON.stringify((diagnostics as Record<string, unknown>).runtime ?? null)}\n- day_payload_summary: ${JSON.stringify(diagnostics.day_payload_summary)}\n\nLookup events: feed.debug, day_brief.response_returned\n`, "utf8");
      console.log(`DAY_LIVE_CANARY_LOOKUP ${JSON.stringify(diagnostics.lookup_tuple)}`);
      console.log(`DAY_LIVE_CANARY_ARTIFACTS ${artifactDir}`);
      hygiene.dispose();
    }
  });
});
