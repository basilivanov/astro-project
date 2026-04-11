"use client";

import { useEffect, useState } from "react";

import { CorrelationManager } from "../lib/correlation";
import {
  waitForTelegramWebAppRuntime,
  type TelegramBootstrapDiagnostics,
  type TelegramBootstrapOutcome,
  type TelegramMode,
  type TelegramRuntimeOverride,
  type TelegramUser,
  type TelegramWebApp,
} from "../lib/telegram-runtime";

type UseTelegramResult = {
  user: TelegramUser | null;
  webApp: TelegramWebApp | null;
  initData: string;
  isReady: boolean;
  mode: TelegramMode;
  correlationId: string | null;
  flowId: string;
  bootstrapOutcome: TelegramBootstrapOutcome["kind"] | null;
  bootstrapDiagnostics: TelegramBootstrapDiagnostics | null;
  onClose: () => void;
};

const MOCK_INIT_DATA = "123456789";
const MOCK_USER: TelegramUser = {
  id: 123456789,
  first_name: "Debug",
  last_name: "User",
  username: "dev_user",
  language_code: "ru",
  photo_url: "",
};

function isLocalMockHost(hostname: string) {
  return hostname === "localhost"
    || hostname === "127.0.0.1"
    || hostname === "0.0.0.0"
    || hostname.endsWith(".local");
}

function mockHelperLaneEnabled() {
  const runtimeEnvironment = (process.env.NEXT_PUBLIC_ENVIRONMENT || process.env.NODE_ENV || "").toLowerCase();
  if (runtimeEnvironment && runtimeEnvironment !== "production") {
    return true;
  }

  if (typeof window !== "undefined" && isLocalMockHost(window.location.hostname)) {
    return true;
  }

  return false;
}

// START_MODULE_CONTRACT: M-USE-TELEGRAM
// purpose: Normalize Telegram WebApp runtime into a stable client hook contract.
// owns:
//   - frontend/hooks/useTelegram.ts
// inputs:
//   - browser location query params, Telegram WebApp globals, optional mock overrides
// outputs:
//   - user/webApp/initData/isReady/mode state for consumer pages
// dependencies:
//   - browser window, sessionStorage, Telegram WebApp runtime
// invariants:
//   - hook always resolves `isReady` after client bootstrap attempt
//   - signed Telegram WebApp initData is the canonical authenticated runtime
//   - mock and guest modes remain explicit helper/public lanes for non-production consumers
// non_goals:
//   - analytics dispatch or API fetching
// END_MODULE_CONTRACT: M-USE-TELEGRAM

// START_MODULE_MAP: M-USE-TELEGRAM
// entrypoints:
//   - useTelegram
// adjacent_modules:
//   - frontend/app/profile/page.tsx
//   - frontend/app/profile/edit/page.tsx
// END_MODULE_MAP: M-USE-TELEGRAM

// START_CONTRACT: FN-USE-TELEGRAM
// purpose: Detect Telegram, mock, guest, or absent runtime and expose a stable client state object.
// returns: UseTelegramResult with explicit mode and ready flag.
// side_effects: reads window/sessionStorage and may invoke Telegram WebApp `ready()`.
// END_CONTRACT: FN-USE-TELEGRAM
export function useTelegram(): UseTelegramResult {
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [webApp, setWebApp] = useState<TelegramWebApp | null>(null);
  const [initData, setInitData] = useState<string>("");
  const [isReady, setIsReady] = useState(false);
  const [mode, setMode] = useState<TelegramMode>("none");
  const [correlationId, setCorrelationId] = useState<string | null>(null);
  const [flowId, setFlowId] = useState<string>("FLOW-HOME-FEED");
  const [bootstrapOutcome, setBootstrapOutcome] = useState<TelegramBootstrapOutcome["kind"] | null>(null);
  const [bootstrapDiagnostics, setBootstrapDiagnostics] = useState<TelegramBootstrapDiagnostics | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const run = async () => {
    try {
      // START_BLOCK: RUNTIME_DETECTION
      const params = new URLSearchParams(window.location.search);
      const flowSeed = params.get("flow") || params.get("flow_id") || "FLOW-HOME-FEED";
      const existingCorrelationId = params.get("correlation_id") || CorrelationManager.getCorrelationId();
      const resolvedCorrelationId = existingCorrelationId || CorrelationManager.newCorrelation(flowSeed);
      CorrelationManager.setCorrelationId(resolvedCorrelationId, { flowId: flowSeed, reason: "useTelegram.bootstrap" });
      setCorrelationId(resolvedCorrelationId);
      setFlowId(flowSeed);
      const runtimeOverride = (window as typeof window & { __TEST_TELEGRAM_RUNTIME__?: TelegramRuntimeOverride }).__TEST_TELEGRAM_RUNTIME__;
      const telegramRuntime = (window as typeof window & { Telegram?: { WebApp?: TelegramWebApp } }).Telegram?.WebApp;
      if (process.env.NODE_ENV !== "production") {
        console.info("[useTelegram.bootstrap]", {
          hasRuntimeOverride: Boolean(runtimeOverride?.initData),
          runtimeOverrideInitDataLength: runtimeOverride?.initData?.length ?? 0,
          hasTelegramRuntime: Boolean(telegramRuntime),
          telegramInitDataLength: telegramRuntime?.initData?.length ?? 0,
        });
      }
      const helperLaneEnabled = mockHelperLaneEnabled();
      const hasMockSession = window.sessionStorage.getItem("mock_telegram_user") === "1";
      const mockParam = params.get("mock");
      const hasMockQuery = mockParam === "1";
      const hasMockInitData = telegramRuntime?.initData === MOCK_INIT_DATA;
      const forceDisableMock = mockParam === "0";
      const hasCanonicalRuntimeOverride = Boolean(runtimeOverride?.initData && runtimeOverride.initData !== MOCK_INIT_DATA);
      const hasCanonicalTelegramRuntime = Boolean(telegramRuntime?.initData && telegramRuntime.initData !== MOCK_INIT_DATA);
      const allowExplicitMockLane = !forceDisableMock && helperLaneEnabled && hasMockQuery;
      const allowImplicitMockLane =
        !forceDisableMock
        && helperLaneEnabled
        && !hasCanonicalRuntimeOverride
        && !hasCanonicalTelegramRuntime
        && (hasMockSession || hasMockInitData);
      const isGuest = params.get("guest") === "1";
      // END_BLOCK: RUNTIME_DETECTION

      // START_BLOCK: MODE_RESOLUTION
      if (isGuest) {
        setMode("guest");
        return;
      }

      if (allowExplicitMockLane || allowImplicitMockLane) {
        window.sessionStorage.setItem("mock_telegram_user", "1");
        const overrideData = (window as typeof window & { MOCK_INIT_DATA_OVERRIDE?: string }).MOCK_INIT_DATA_OVERRIDE;
        const overrideUser = (window as typeof window & { MOCK_USER_OVERRIDE?: TelegramUser }).MOCK_USER_OVERRIDE;
        setUser(overrideUser || MOCK_USER);
        setInitData(overrideData || telegramRuntime?.initData || MOCK_INIT_DATA);
        setWebApp(telegramRuntime || null);
        setMode("mock");
        return;
      }

      window.sessionStorage.removeItem("mock_telegram_user");

      const bootstrap = await waitForTelegramWebAppRuntime();
      setBootstrapOutcome(bootstrap.outcome.kind);
      setBootstrapDiagnostics(bootstrap.diagnostics);

      if (process.env.NODE_ENV !== "production") {
        console.info("[useTelegram.bootstrap]", bootstrap.diagnostics);
      }

      if (bootstrap.mode === "telegram") {
        bootstrap.webApp?.ready?.();
        bootstrap.webApp?.expand?.();
        setWebApp(bootstrap.webApp);
        setInitData(bootstrap.initData);
        setUser(bootstrap.user);
        setMode("telegram");
      } else {
        setMode("none");
      }
      // END_BLOCK: MODE_RESOLUTION
    } catch {
      setMode("none");
    } finally {
      setIsReady(true);
    }
    };

    void run();
  }, []);

  return { user, webApp, initData, isReady, mode, correlationId, flowId, bootstrapOutcome, bootstrapDiagnostics, onClose: () => webApp?.close?.() };
}
