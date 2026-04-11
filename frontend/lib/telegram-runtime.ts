export type TelegramMode = "telegram" | "mock" | "guest" | "none";

export type TelegramUser = {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
};

export type TelegramWebApp = {
  initData?: string;
  initDataUnsafe?: {
    user?: TelegramUser | null;
  };
  ready?: () => void;
  expand?: () => void;
  close?: () => void;
};

export type TelegramRuntimeOverride = {
  user?: TelegramUser | null;
  initData?: string;
};

export type TelegramBootstrapOutcome =
  | { kind: "ready" | "late_ready"; source: "telegram" | "test_runtime"; elapsedMs: number; initDataLength: number; userId?: number; webAppPresent: boolean }
  | { kind: "runtime_missing"; elapsedMs: number; webAppPresent: boolean }
  | { kind: "initdata_missing"; elapsedMs: number; webAppPresent: boolean };

export type TelegramBootstrapDiagnostics = {
  href: string;
  search: string;
  hash: string;
  readyState: string;
  telegramPresent: boolean;
  webAppPresent: boolean;
  initDataLength: number;
  userId: number | null;
  elapsedMs: number;
  outcome: TelegramBootstrapOutcome["kind"];
};

export type TelegramBootstrapResolved = {
  mode: TelegramMode;
  user: TelegramUser | null;
  webApp: TelegramWebApp | null;
  initData: string;
  outcome: TelegramBootstrapOutcome;
  diagnostics: TelegramBootstrapDiagnostics;
};

const MOCK_INIT_DATA = "123456789";

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function getRuntimeSnapshot() {
  const win = window as typeof window & {
    __TEST_TELEGRAM_RUNTIME__?: TelegramRuntimeOverride;
    Telegram?: { WebApp?: TelegramWebApp };
  };
  const runtimeOverride = win.__TEST_TELEGRAM_RUNTIME__;
  const webApp = win.Telegram?.WebApp ?? null;
  const overrideInitData = runtimeOverride?.initData ?? "";
  const webAppInitData = webApp?.initData ?? "";
  const resolvedInitData = overrideInitData && overrideInitData !== MOCK_INIT_DATA ? overrideInitData : webAppInitData;
  const resolvedUser = (overrideInitData && overrideInitData !== MOCK_INIT_DATA ? runtimeOverride?.user : webApp?.initDataUnsafe?.user) ?? runtimeOverride?.user ?? null;
  const source = overrideInitData && overrideInitData !== MOCK_INIT_DATA ? "test_runtime" : "telegram";
  return {
    runtimeOverride,
    webApp,
    source: source as "telegram" | "test_runtime",
    initData: resolvedInitData,
    user: resolvedUser ?? null,
    telegramPresent: Boolean(win.Telegram),
    webAppPresent: Boolean(webApp),
  };
}

export async function waitForTelegramWebAppRuntime(options?: { timeoutMs?: number; intervalMs?: number }) {
  const timeoutMs = options?.timeoutMs ?? 4000;
  const intervalMs = options?.intervalMs ?? 150;
  const startedAt = Date.now();
  let sawRuntime = false;

  while (Date.now() - startedAt <= timeoutMs) {
    const snapshot = getRuntimeSnapshot();
    sawRuntime = sawRuntime || snapshot.webAppPresent || snapshot.telegramPresent;
    if (snapshot.initData && snapshot.initData !== MOCK_INIT_DATA) {
      const elapsedMs = Date.now() - startedAt;
      const outcome: TelegramBootstrapOutcome = {
        kind: elapsedMs > intervalMs ? "late_ready" : "ready",
        source: snapshot.source,
        elapsedMs,
        initDataLength: snapshot.initData.length,
        userId: snapshot.user?.id,
        webAppPresent: snapshot.webAppPresent,
      };
      return {
        mode: "telegram" as const,
        user: snapshot.user,
        webApp: snapshot.webApp,
        initData: snapshot.initData,
        outcome,
        diagnostics: {
          href: window.location.href,
          search: window.location.search,
          hash: window.location.hash,
          readyState: document.readyState,
          telegramPresent: snapshot.telegramPresent,
          webAppPresent: snapshot.webAppPresent,
          initDataLength: snapshot.initData.length,
          userId: snapshot.user?.id ?? null,
          elapsedMs,
          outcome: outcome.kind,
        },
      } satisfies TelegramBootstrapResolved;
    }
    await sleep(intervalMs);
  }

  const snapshot = getRuntimeSnapshot();
  const elapsedMs = Date.now() - startedAt;
  const outcome: TelegramBootstrapOutcome = snapshot.webAppPresent || sawRuntime
    ? { kind: "initdata_missing", elapsedMs, webAppPresent: snapshot.webAppPresent }
    : { kind: "runtime_missing", elapsedMs, webAppPresent: false };
  return {
    mode: "none" as const,
    user: null,
    webApp: snapshot.webApp,
    initData: "",
    outcome,
    diagnostics: {
      href: window.location.href,
      search: window.location.search,
      hash: window.location.hash,
      readyState: document.readyState,
      telegramPresent: snapshot.telegramPresent,
      webAppPresent: snapshot.webAppPresent,
      initDataLength: 0,
      userId: null,
      elapsedMs,
      outcome: outcome.kind,
    },
  } satisfies TelegramBootstrapResolved;
}
