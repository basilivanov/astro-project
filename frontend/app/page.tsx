"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "../hooks/useTelegram";
import { LandingContent } from "../components/landing/LandingContent";
import { EmptyState, ErrorState, LoadingState } from "../components/ui-states";
import {
  ConsumerHero,
  ConsumerMetaPill,
  ConsumerPageShell,
  ConsumerPanel,
} from "../components/consumer-page-shell";
import { HOME_FLOW_ID, ensureHomeCorrelation, homeFetch, makeHomeTrace, trackHomeEvent } from "../lib/home-analytics";
import { normalizeDayBriefPayload, type TodayViewModel } from "../lib/day-brief";
import {
  TodayCtaPanel,
  TodayScores,
  TodayVerdict,
} from "../components/today/daybrief-sections";

// START_MODULE_CONTRACT: M-HOME-FEED
// purpose: Render the home feed surface under strict GRACE with correlated telemetry and semantic feed blocks.
// owns:
//   - frontend/app/page.tsx
// inputs:
//   - Telegram runtime context, user profile, daily feed API, mock overrides
// outputs:
//   - Home feed hero, fallback and deeper CTA surfaces with correlated analytics
// dependencies:
//   - useTelegram, home analytics helper, consumer page shell, day brief adapter
// invariants:
//   - home telemetry uses flow_id=FLOW-HOME-FEED with surface=home
//   - feed states map to semantic blocks with data-testid wrappers
//   - CTA handlers and score taps emit correlated trace metadata
// failure_policy:
//   - API failures downgrade to fallback/empty/error surfaces without crashing the shell
// non_goals:
//   - week/catalog business logic beyond navigation and telemetry handoff
// END_MODULE_CONTRACT: M-HOME-FEED

type FeedState = "ready" | "empty" | "error" | "no_data";
type FeedSurfaceState = FeedState | "loading" | "error";
type MockFeedStateOverride = FeedState | undefined;

type ProfileViewModel = {
  full_name?: string | null;
  birth_date?: string | null;
  subscription_active_until?: string | null;
  referral_code?: string | null;
};

type MockWindow = Window & {
  MOCK_FEED_OVERRIDE?: unknown;
  MOCK_FEED_STATE?: MockFeedStateOverride;
  MOCK_PROFILE_OVERRIDE?: unknown;
};

type FeedLayoutProps = {
  children: ReactNode;
  profile?: ProfileViewModel | null;
  state: FeedSurfaceState;
  dateLabel?: string;
  today?: TodayViewModel | null;
  renderPath?: "canonical" | "error" | "no_data" | "empty";
};

const HOME_CONTRACTS = {
  bootstrap: "FN-BOOTSTRAP-HOME-FEED",
  load: "FN-LOAD-HOME-FEED",
  cta: "FN-HANDLE-HOME-CTA",
  scoreTap: "FN-HANDLE-HOME-SCORE-TAP",
  mockToggle: "FN-HANDLE-HOME-MOCK-TOGGLE",
} as const;

function normalizeProfile(payload: unknown): ProfileViewModel {
  if (!payload || typeof payload !== "object") {
    return {};
  }
  const data = payload as Record<string, unknown>;
  return {
    full_name: typeof data.full_name === "string" ? data.full_name : null,
    birth_date: typeof data.birth_date === "string" ? data.birth_date : null,
    subscription_active_until: typeof data.subscription_active_until === "string" ? data.subscription_active_until : null,
    referral_code: typeof data.referral_code === "string" ? data.referral_code : null,
  };
}

function normalizeMockProfile(payload: unknown): ProfileViewModel {
  const base: ProfileViewModel = {
    full_name: "Debug User",
    birth_date: "2000-01-01",
    subscription_active_until: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    referral_code: "DEBUG123",
  };
  if (!payload || typeof payload !== "object") {
    return base;
  }
  return { ...base, ...normalizeProfile(payload) };
}

function resolveMockToday(mockState: MockFeedStateOverride, mockFeed: unknown, profile: ProfileViewModel | null): { nextToday: TodayViewModel | null; nextFeedState: FeedState; nextError: string | null } {
  switch (mockState) {
    case "empty":
      return { nextToday: null, nextFeedState: "empty", nextError: null };
    case "error":
      return { nextToday: null, nextFeedState: "error", nextError: "Не удалось загрузить астросводку" };
    case "no_data": {
      const nextToday = normalizeDayBriefPayload(mockFeed ?? {}, profile);
      return { nextToday, nextFeedState: nextToday?.state ?? "no_data", nextError: null };
    }
    default: {
      const nextToday = normalizeDayBriefPayload(mockFeed ?? {}, profile);
      return { nextToday, nextFeedState: nextToday?.state ?? "empty", nextError: null };
    }
  }
}

async function fetchJson(url: string, init?: RequestInit, block?: string) {
  const response = await homeFetch(url, init, block);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function toErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  if (typeof error === "string" && error.trim()) {
    return error;
  }
  return fallback;
}

function FeedLayout({ children, profile, state, dateLabel, today, renderPath }: FeedLayoutProps) {
  const heroLabel = today?.brief.hero?.title ?? "";
  const shouldRenderHero = Boolean(today?.brief.hero);
  return (
    <ConsumerPageShell
      testId="home-feed-page"
      analyticsEvent={{
        event_name: "home.feed_shell_view",
        payload: {
          ...makeHomeTrace({ contract: "FN-CONSUMER-PAGE-SHELL", block: "SHELL_RENDER" }),
          state,
          surface: "home",
        },
      }}
    >
      {process.env.NODE_ENV !== "production" ? (
        <div hidden data-testid="today-render-path" data-render-path={renderPath ?? "empty"}>
          {renderPath ?? "empty"}
        </div>
      ) : null}
      {shouldRenderHero ? (
        <ConsumerHero
          eyebrow={dateLabel ?? ""}
          title={heroLabel}
          meta={<ConsumerMetaPill label="Дата" value={dateLabel ?? ""} />}
        />
      ) : null}
      {children}
    </ConsumerPageShell>
  );
}

export default function FeedPage() {
  const router = useRouter();
  const { isReady, user, initData, mode, bootstrapOutcome, bootstrapDiagnostics } = useTelegram();
  const correlationId = useMemo(() => ensureHomeCorrelation(), []);
  const isMockHelperLane = mode === "mock";
  const isCanonicalTelegramLane = mode === "telegram" && Boolean(user) && Boolean(initData);
  const shouldShowLanding = !isMockHelperLane && !isCanonicalTelegramLane;
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<ProfileViewModel | null>(null);
  const [today, setToday] = useState<TodayViewModel | null>(null);
  const [feedState, setFeedState] = useState<FeedState>("ready");
  const [error, setError] = useState<string | null>(null);
  const [bootstrapTimedOut, setBootstrapTimedOut] = useState(false);
  const [recoveryRedirectScheduled, setRecoveryRedirectScheduled] = useState(false);

  useEffect(() => {
    if (process.env.NODE_ENV === "production") {
      return;
    }
    console.info("[home-runtime]", {
      mode,
      isReady,
      hasUser: Boolean(user),
      hasInitData: Boolean(initData),
      initDataLength: initData.length,
      href: typeof window !== "undefined" ? window.location.href : null,
    });
  }, [mode, isReady, user, initData]);

  useEffect(() => {
    if (isReady) {
      setBootstrapTimedOut(false);
      return;
    }

    const timer = window.setTimeout(() => {
      setBootstrapTimedOut(true);
    }, 4000);

    return () => window.clearTimeout(timer);
  }, [isReady]);

  useEffect(() => {
    const needsRecoveryHandoff = isReady && !isCanonicalTelegramLane && (bootstrapOutcome === "runtime_missing" || bootstrapOutcome === "initdata_missing");
    if (!needsRecoveryHandoff) {
      setRecoveryRedirectScheduled(false);
      return;
    }
    setRecoveryRedirectScheduled(true);
    const reason = bootstrapOutcome ?? "runtime_missing";
    const timer = window.setTimeout(() => {
      router.replace(`/start?recovery=${reason}`);
    }, 1500);
    return () => window.clearTimeout(timer);
  }, [bootstrapOutcome, isCanonicalTelegramLane, isReady, router]);

  const emitHomeEvent = useCallback(async (eventName: string, block: string, semanticBlock: string, meta: Record<string, unknown>) => {
    await trackHomeEvent(
      eventName,
      {
        ...makeHomeTrace({ contract: HOME_CONTRACTS.load, block, semantic_block: semanticBlock, correlation_id: correlationId }),
        ...meta,
      },
      { correlationId, flowId: HOME_FLOW_ID, block },
    );
  }, [correlationId]);

  const loadFeedPage = useCallback(async () => {
    if (!isCanonicalTelegramLane || !user || !initData) {
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const profileRequest = fetchJson("/api/users/me", { headers: { "X-Telegram-Auth": initData } }, "PROFILE_LOAD")
        .then((payload) => {
          const nextProfile = normalizeProfile(payload);
          setProfile(nextProfile);
          return nextProfile;
        })
        .catch(() => null);

      const feedResult = await fetchJson("/api/feed/today", { headers: { "X-Telegram-Auth": initData } }, "FEED_LOAD");
      const nextProfile = await Promise.race([
        profileRequest,
        Promise.resolve(profile),
      ]);

      {
        const nextToday = normalizeDayBriefPayload(feedResult, nextProfile);
        if (nextToday) {
          setToday(nextToday);
          setFeedState(nextToday.state);
          await emitHomeEvent("today.brief_view", "FEED_LOAD_SUCCESS", "DAY_BRIEF_VIEW", {
            contract: HOME_CONTRACTS.load,
            status: nextToday.state,
            entry_point: "home-feed-api",
            personalization_level: nextToday.brief.personalization_level,
            premium_active: nextToday.brief.premium?.subscription_active ?? false,
          });
        } else {
          setToday(null);
          setFeedState("empty");
          await emitHomeEvent("home.feed_load_empty", "FEED_LOAD_EMPTY", "FEED_LOAD_EMPTY", {
            contract: HOME_CONTRACTS.load,
            status: "empty",
            entry_point: "home-feed-api",
          });
        }
      }

      void profileRequest.then((resolvedProfile) => {
        if (!resolvedProfile) {
          return;
        }

        setToday((currentToday) => {
          if (!currentToday) {
            return currentToday;
          }
          return normalizeDayBriefPayload(feedResult, resolvedProfile) ?? currentToday;
        });
      });
    } catch (err) {
      setProfile(null);
      setToday(null);
      setFeedState("empty");
      const message = toErrorMessage(err, "Не удалось загрузить астросводку");
      setError(message);
      await emitHomeEvent("home.feed_load_error", "FEED_LOAD_ERROR", "FEED_LOAD_ERROR", {
        contract: HOME_CONTRACTS.load,
        status: "error",
        entry_point: "home-feed-api",
        message,
      });
    } finally {
      setLoading(false);
    }
  }, [emitHomeEvent, initData, isCanonicalTelegramLane, user]);

  useEffect(() => {
    if (!isReady) {
      return;
    }

    void trackHomeEvent(
      "home.feed_bootstrap",
      {
        ...makeHomeTrace({ contract: HOME_CONTRACTS.bootstrap, block: "FEED_BOOTSTRAP", semantic_block: "FEED_BOOTSTRAP", correlation_id: correlationId }),
        entry_point: "home-surface-init",
        mode,
        ready: isReady,
        user_id: user?.id,
      },
      { correlationId, flowId: HOME_FLOW_ID, block: "FEED_BOOTSTRAP" },
    );

    if (isMockHelperLane) {
      const mockWindow = window as MockWindow;
      const nextProfile = normalizeMockProfile(mockWindow.MOCK_PROFILE_OVERRIDE);
      const { nextToday, nextFeedState, nextError } = resolveMockToday(mockWindow.MOCK_FEED_STATE, mockWindow.MOCK_FEED_OVERRIDE, nextProfile);
      setProfile(nextProfile);
      setToday(nextToday);
      setFeedState(nextFeedState);
      setError(nextError);
      setLoading(false);
      void trackHomeEvent(
        "home.feed_mock_state",
        {
          ...makeHomeTrace({ contract: HOME_CONTRACTS.mockToggle, block: "FEED_BOOTSTRAP", semantic_block: "FEED_BOOTSTRAP", correlation_id: correlationId }),
          entry_point: "home-feed-mock-toggle",
          status: nextError ? "error" : nextFeedState,
          mock_feed_state: nextFeedState,
        },
        { correlationId, flowId: HOME_FLOW_ID, block: "FEED_BOOTSTRAP" },
      );
      return;
    }

    if (isCanonicalTelegramLane && user && initData) {
      void loadFeedPage();
      return;
    }

    setLoading(false);
  }, [correlationId, initData, isCanonicalTelegramLane, isMockHelperLane, isReady, loadFeedPage, mode, user]);

  const handleHomeCta = useCallback((ctaId: string, href: string, entryPoint: string, block: string) => {
    void trackHomeEvent(
      block === "CTA_PRIMARY" ? "today.cta_click" : "today.cta_secondary_click",
      {
        ...makeHomeTrace({ contract: HOME_CONTRACTS.cta, block, semantic_block: block, correlation_id: correlationId }),
        entry_point: entryPoint,
        cta_id: ctaId,
        href,
        status: "click",
      },
      { correlationId, flowId: HOME_FLOW_ID, block },
    );
  }, [correlationId]);

  const handleScoreTap = useCallback((scoreKey: string, scoreValue: number) => {
    void trackHomeEvent(
      "today.score_tap",
      {
        ...makeHomeTrace({ contract: HOME_CONTRACTS.scoreTap, block: "DAY_BRIEF_SCORES", semantic_block: "DAY_BRIEF_SCORES", correlation_id: correlationId }),
        score_key: scoreKey,
        score_value: scoreValue,
      },
      { correlationId, flowId: HOME_FLOW_ID, block: "DAY_BRIEF_SCORES" },
    );
  }, [correlationId]);


  if (!isReady || loading) {
    const shouldShowBootstrapDebug = !isReady && bootstrapTimedOut;
    return (
      <FeedLayout state="loading" profile={profile} today={today} renderPath="empty">
        <ConsumerPanel className="p-5">
          {shouldShowBootstrapDebug ? (
            <EmptyState
              compact
              title={bootstrapOutcome === "initdata_missing" ? "Telegram не передал initData" : "Telegram runtime не инициализировался"}
              message={bootstrapOutcome === "initdata_missing"
                ? "Mini App открылась, но Telegram не передал initData. Перейди через /start, чтобы повторить bootstrap."
                : "Приложение открылось, но Telegram WebApp не инициализировался вовремя. Открой экран заново через /start или обнови mini app."}
              actionLabel={recoveryRedirectScheduled ? "Переходим в /start…" : "Открыть /start"}
              actionHref={`/start?recovery=${bootstrapOutcome ?? "runtime_missing"}`}
              actionTestId="home-bootstrap-recover-cta"
            />
          ) : (
            <LoadingState compact message="Собираем сводку дня" />
          )}
          {process.env.NODE_ENV !== "production" ? (
            <div hidden data-testid="home-runtime-diagnostics"
              data-mode={mode}
              data-is-ready={String(isReady)}
              data-has-user={String(Boolean(user))}
              data-has-init-data={String(Boolean(initData))}
              data-init-data-length={String(initData.length)}
              data-bootstrap-timed-out={String(bootstrapTimedOut)}
              data-bootstrap-outcome={bootstrapOutcome ?? "unknown"}
              data-bootstrap-href={bootstrapDiagnostics?.href ?? ""}
              data-bootstrap-hash={bootstrapDiagnostics?.hash ?? ""}
              data-recovery-redirect-scheduled={String(recoveryRedirectScheduled)}
            />
          ) : null}
        </ConsumerPanel>
      </FeedLayout>
    );
  }

  if (shouldShowLanding) {
    return <LandingContent />;
  }

  if (error) {
    return (
      <FeedLayout state="error" profile={profile} today={today} renderPath="error">
        <ConsumerPanel className="p-5">
          <ErrorState compact error={error} />
        </ConsumerPanel>
      </FeedLayout>
    );
  }

  if (!today) {
    return (
      <FeedLayout state={feedState} profile={profile} today={today} renderPath="empty">
        <ConsumerPanel className="p-5">
          <EmptyState
            compact
            title="Нет данных на сегодня"
            message="Для сегодняшней карты пока нет канонических данных по четырём сферам."
          />
        </ConsumerPanel>
      </FeedLayout>
    );
  }

  if (today.state === "error") {
    return (
      <FeedLayout state="error" profile={profile} dateLabel={today.brief.date} today={today} renderPath="error">
        <ConsumerPanel className="p-5" data-testid="today-error-state">
          <EmptyState
            compact
            title="Ошибка расчёта дня"
            message="Каноническая карта дня не собрана. Доступна только неделя или история разборов."
          />
          <p className="mt-4 text-center text-xs leading-relaxed text-slate-500" data-testid="today-error-note">
            Экран не подменяется fallback-текстом и ждёт новый расчёт.
          </p>
        </ConsumerPanel>
      </FeedLayout>
    );
  }

  if (today.state === "no_data") {
    return (
      <FeedLayout state="empty" profile={profile} dateLabel={today.brief.date} today={today} renderPath="no_data">
        <ConsumerPanel className="p-5" data-testid="today-no-data-state">
          <EmptyState
            compact
            title="Нет данных на сегодня"
            message="По одной или нескольким сферам нет канонических текстов и оценок."
          />
          <p className="mt-4 text-center text-xs leading-relaxed text-slate-500" data-testid="today-no-data-note">
            Экран остаётся честно пустым, пока не появится полный дневной расчёт.
          </p>
        </ConsumerPanel>
      </FeedLayout>
    );
  }

  return (
    <FeedLayout
      state={feedState}
      profile={profile}
      dateLabel={today.brief.date}
      today={today}
      renderPath="canonical"
    >
      <div className="space-y-4">
        <TodayVerdict brief={today.brief} />
        <TodayScores brief={today.brief} onScoreTap={handleScoreTap} />
        <TodayCtaPanel brief={today.brief} onCta={handleHomeCta} />
      </div>
    </FeedLayout>
  );
}
