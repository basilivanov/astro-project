"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { LoadingState } from "../../components/ui-states";
import { trackCatalogEvent } from "../../components/catalog/catalog-analytics";
import { CATALOG_GRACE_MODULES, withCatalogTrace } from "../../components/catalog/create-shared";
import { CorrelationManager, correlatedFetch } from "../../lib/correlation";
import { useTelegram } from "../../hooks/useTelegram";

const FLOW_HOME_FEED = "FLOW-HOME-FEED";
const START_BLOCKS = {
  gate: "START_GATE",
  authWait: "AUTH_WAIT",
  profileRoute: "PROFILE_ROUTE",
} as const;

const START_MODULE_CONTRACT = {
  module: "M-START-GATEWAY",
  purpose: "Resolve /start as the strict GRACE gateway between guest, mocked, and authenticated feed/onboarding routes.",
  inputs: ["telegram context from useTelegram", "browser query/runtime mode metadata"],
  outputs: ["redirect decision to feed, onboarding, or auth wait UI"],
  trace_obligations: {
    flow_id: FLOW_HOME_FEED,
    block_labels: [START_BLOCKS.gate, START_BLOCKS.authWait, START_BLOCKS.profileRoute],
  },
} as const;

const START_MODULE_MAP = {
  entrypoints: ["StartPage"],
  semantic_blocks: ["resolveMockRedirect", "handleAuthWait", "ensureProfileCompletion"],
  adjacent_modules: [
    "frontend/hooks/useTelegram.ts",
    "frontend/components/catalog/catalog-analytics.ts",
    "frontend/lib/correlation.ts",
  ],
} as const;

type StartStatus = "init" | "waiting_auth" | "checking_profile";

type RedirectTarget = "/?mock=1" | "/" | "/onboarding/profile";

function buildTrace(
  correlationId: string,
  flowId: string,
  contract: string,
  block: string,
  extras: Record<string, unknown> = {},
) {
  return withCatalogTrace(
    {
      flow_id: flowId,
      correlation_id: correlationId,
      ...extras,
    },
    {
      module: CATALOG_GRACE_MODULES.analytics,
      contract,
      block,
      semantic_block: block,
      correlation_id: correlationId,
    },
  );
}

// START_MODULE_CONTRACT: M-START-GATEWAY
// purpose: Resolve /start as strict GRACE guest/mock/auth gateway with telemetry-backed redirect decisions.
// owns:
//   - frontend/app/start/page.tsx
// inputs:
//   - telegram context from `useTelegram`
//   - browser runtime/query params used to derive guest/mock/authenticated state
// outputs:
//   - auth wait UI with test hooks
//   - redirect decisions to `/`, `/?mock=1`, `/onboarding/profile`
// dependencies:
//   - frontend/hooks/useTelegram.ts
//   - frontend/components/catalog/catalog-analytics.ts
//   - frontend/lib/correlation.ts
// invariants:
//   - every redirect/auth gate decision emits GRACE-aligned telemetry with `FLOW-HOME-FEED`
//   - semantic blocks remain addressable as START_GATE, AUTH_WAIT, PROFILE_ROUTE
// non_goals:
//   - rendering feed/onboarding business content
// END_MODULE_CONTRACT: M-START-GATEWAY

// START_MODULE_MAP: M-START-GATEWAY
// entrypoints:
//   - StartPage
// semantic_blocks:
//   - resolveMockRedirect
//   - handleAuthWait
//   - ensureProfileCompletion
// owned_tests:
//   - frontend/e2e/landing.spec.ts
//   - frontend/e2e/start-gateway.spec.ts
// adjacent_modules:
//   - frontend/hooks/useTelegram.ts
//   - frontend/components/catalog/create-shared.ts
//   - frontend/lib/analytics.ts
// END_MODULE_MAP: M-START-GATEWAY

// START_CONTRACT: FN-RESOLVE-MOCK-REDIRECT
// purpose: Route mock/browser sessions into feed and emit redirect telemetry.
// inputs: router, correlation id setter, redirect target.
// returns: cleanup function for redirect fallback timer.
// side_effects: navigation + telemetry dispatch.
// END_CONTRACT: FN-RESOLVE-MOCK-REDIRECT
function resolveMockRedirect(router: ReturnType<typeof useRouter>, correlationId: string) {
  // START_BLOCK: START_GATE
  const nextUrl: RedirectTarget = "/?mock=1";
  const expectedMockUrl = new URL(nextUrl, window.location.origin).toString();
  void trackCatalogEvent(
    "start.redirect_decision",
    buildTrace(correlationId, FLOW_HOME_FEED, "FN-RESOLVE-MOCK-REDIRECT", START_BLOCKS.gate, {
      action: "redirect",
      surface: "catalog",
      entry_point: "/start",
      target_path: nextUrl,
      decision: "mock_feed",
      start_contract: START_MODULE_CONTRACT.module,
      start_map_entrypoint: START_MODULE_MAP.entrypoints[0],
    }),
    { correlationId, flowId: FLOW_HOME_FEED, block: START_BLOCKS.gate },
  );
  router.replace(nextUrl);
  const fallback = window.setTimeout(() => {
    const currentUrl = new URL(window.location.href);
    const isExpectedMockFeed = currentUrl.toString() === expectedMockUrl;
    if (!isExpectedMockFeed) {
      window.location.assign(nextUrl);
    }
  }, 400);
  return () => window.clearTimeout(fallback);
  // END_BLOCK: START_GATE
}

// START_CONTRACT: FN-HANDLE-AUTH-WAIT
// purpose: Put /start into explicit auth wait state and log visible CTA gating.
// inputs: correlation id, mode, ready state.
// returns: `waiting_auth` UI state.
// side_effects: telemetry dispatch.
// END_CONTRACT: FN-HANDLE-AUTH-WAIT
function handleAuthWait(correlationId: string, mode: string, isReady: boolean): StartStatus {
  // START_BLOCK: AUTH_WAIT
  void trackCatalogEvent(
    "start.auth_wait",
    buildTrace(correlationId, FLOW_HOME_FEED, "FN-HANDLE-AUTH-WAIT", START_BLOCKS.authWait, {
      action: "auth_wait",
      surface: "catalog",
      entry_point: "/start",
      telegram_mode: mode,
      telegram_ready: isReady,
      decision: "show_auth_wait",
    }),
    { correlationId, flowId: FLOW_HOME_FEED, block: START_BLOCKS.authWait },
  );
  return "waiting_auth";
  // END_BLOCK: AUTH_WAIT
}

// START_CONTRACT: FN-ENSURE-PROFILE-COMPLETION
// purpose: Resolve authenticated users into feed or onboarding based on backend profile completeness.
// inputs: telegram initData, correlation id, router.
// returns: cleanup function or void.
// side_effects: API request, redirect, telemetry dispatch.
// failure_mode: falls back to onboarding redirect on auth/network failure.
// END_CONTRACT: FN-ENSURE-PROFILE-COMPLETION
function ensureProfileCompletion(
  router: ReturnType<typeof useRouter>,
  initData: string,
  correlationId: string,
) {
  // START_BLOCK: PROFILE_ROUTE
  void trackCatalogEvent(
    "start.profile_check_started",
    buildTrace(correlationId, FLOW_HOME_FEED, "FN-ENSURE-PROFILE-COMPLETION", START_BLOCKS.profileRoute, {
      action: "profile_check_start",
      surface: "catalog",
      entry_point: "/start",
      target_path: "/api/users/me",
    }),
    { correlationId, flowId: FLOW_HOME_FEED, block: START_BLOCKS.profileRoute },
  );

  correlatedFetch(
    "/api/users/me",
    {
      headers: { "X-Telegram-Auth": initData },
    },
    {
      correlationId,
      flowId: FLOW_HOME_FEED,
      block: START_BLOCKS.profileRoute,
    },
  )
    .then((res) => {
      if (res.status === 401) throw new Error("Auth failed");
      if (!res.ok) throw new Error("Network error");
      return res.json();
    })
    .then((data) => {
      const nextUrl: RedirectTarget = data && data.birth_date ? "/" : "/onboarding/profile";
      void trackCatalogEvent(
        "start.profile_redirect",
        buildTrace(correlationId, FLOW_HOME_FEED, "FN-ENSURE-PROFILE-COMPLETION", START_BLOCKS.profileRoute, {
          action: "redirect",
          surface: "catalog",
          entry_point: "/start",
          target_path: nextUrl,
          decision: nextUrl === "/" ? "feed" : "profile_onboarding",
          profile_complete: Boolean(data?.birth_date),
        }),
        { correlationId, flowId: FLOW_HOME_FEED, block: START_BLOCKS.profileRoute },
      );
      router.replace(nextUrl);
    })
    .catch((error) => {
      console.error(error);
      const nextUrl: RedirectTarget = "/onboarding/profile";
      void trackCatalogEvent(
        "start.profile_redirect_failed",
        buildTrace(correlationId, FLOW_HOME_FEED, "FN-ENSURE-PROFILE-COMPLETION", START_BLOCKS.profileRoute, {
          action: "redirect",
          surface: "catalog",
          entry_point: "/start",
          target_path: nextUrl,
          decision: "profile_onboarding_fallback",
          error_message: error instanceof Error ? error.message : "unknown",
        }),
        { correlationId, flowId: FLOW_HOME_FEED, block: START_BLOCKS.profileRoute },
      );
      router.replace(nextUrl);
    });
  // END_BLOCK: PROFILE_ROUTE
}

// START_CONTRACT: FN-START-PAGE
// purpose: Render /start gateway and coordinate auth/mock/profile redirect logic.
// inputs: none.
// returns: auth gate or loading UI.
// side_effects: redirect orchestration, profile fetch, telemetry dispatch.
// END_CONTRACT: FN-START-PAGE
export default function StartPage() {
  const { user, initData, isReady, mode, correlationId, flowId, bootstrapOutcome } = useTelegram();
  const router = useRouter();
  const [status, setStatus] = useState<StartStatus>("init");
  const [effectiveCorrelationId, setEffectiveCorrelationId] = useState<string>("");
  const [retryTick, setRetryTick] = useState(0);
  const recoveryReason = useMemo(() => {
    if (typeof window === "undefined") return null;
    return new URLSearchParams(window.location.search).get("recovery");
  }, [retryTick]);

  const activeFlowId = flowId || FLOW_HOME_FEED;

  useEffect(() => {
    const nextCorrelationId = correlationId || CorrelationManager.ensureCorrelationId();
    CorrelationManager.setCorrelationId(nextCorrelationId, { flowId: activeFlowId, reason: "start.page" });
    setEffectiveCorrelationId(nextCorrelationId);
  }, [correlationId, activeFlowId]);

  useEffect(() => {
    if (!isReady || !effectiveCorrelationId) {
      return;
    }

    if (mode === "mock") {
      setStatus("checking_profile");
      return resolveMockRedirect(router, effectiveCorrelationId);
    }

    if (mode === "guest" || !user || !initData) {
      setStatus(handleAuthWait(effectiveCorrelationId, mode, isReady));
      return;
    }

    setStatus("checking_profile");
    ensureProfileCompletion(router, initData, effectiveCorrelationId);
  }, [user, initData, isReady, mode, router, effectiveCorrelationId]);

  if (status === "waiting_auth") {
    return (
      <div
        data-testid="start-auth-gate"
        data-flow-id={activeFlowId}
        data-correlation-id={effectiveCorrelationId}
        className="flex flex-col items-center justify-center min-h-screen p-6 text-center space-y-6 animate-in fade-in bg-white text-slate-900"
      >
        <div
          data-testid="start-auth-gate-icon"
          className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center text-4xl shadow-sm"
        >
          ✨
        </div>
        <div data-testid="start-auth-gate-copy" className="space-y-2">
          <h1 className="text-2xl font-black text-slate-900">
            {recoveryReason ? "Восстанавливаем запуск Mini App" : "Войти через Telegram"}
          </h1>
          <p className="text-slate-500 max-w-xs mx-auto" data-testid="start-recovery-copy">
            {recoveryReason === "initdata_missing"
              ? "Telegram открыл Mini App, но не передал initData. Попробуйте повторить запуск через этот recovery screen."
              : recoveryReason === "runtime_missing"
                ? "Mini App не получила Telegram runtime вовремя. Этот экран поможет безопасно перезапустить запуск."
                : "Чтобы сохранить ваш прогресс и открыть доступ к прогнозам, нам нужно знать, кто вы."}
          </p>
        </div>
        <button
          data-testid="start-auth-gate-cta"
          onClick={() => {
            void trackCatalogEvent(
              "start.auth_wait_cta_click",
              buildTrace(effectiveCorrelationId, activeFlowId, "FN-HANDLE-AUTH-WAIT", START_BLOCKS.authWait, {
                action: "cta_click",
                cta_id: "start_auth_gate_mock_login",
                cta_href: "/start?mock=1",
                surface: "catalog",
                entry_point: "/start",
              }),
              { correlationId: effectiveCorrelationId, flowId: activeFlowId, block: START_BLOCKS.authWait },
            );
            window.location.href = "/start?mock=1";
          }}
          className="btn bg-blue-500 text-white w-full py-4 rounded-xl font-bold hover:bg-blue-600 transition-colors"
        >
          Тестовый вход (Браузер)
        </button>
        <div className="flex flex-col items-center gap-3">
          <button
            type="button"
            data-testid="start-recovery-retry"
            onClick={() => {
              setRetryTick((value) => value + 1);
              window.location.href = "/start";
            }}
            className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
          >
            Повторить запуск
          </button>
          <p data-testid="start-auth-gate-hint" className="text-xs text-slate-400 mt-2">
            {bootstrapOutcome === "initdata_missing"
              ? "Telegram открыл Mini App, но не передал initData. Нажмите кнопку ещё раз или откройте экран повторно."
              : "Если вы видите этот экран внутри Telegram, попробуйте перезапустить мини-приложение."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      data-testid="start-loading-gate"
      data-flow-id={activeFlowId}
      data-correlation-id={effectiveCorrelationId}
    >
      <LoadingState message={status === "checking_profile" ? "Проверяем профиль..." : "Запуск..."} />
    </div>
  );
}
