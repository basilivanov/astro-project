"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AlertTriangle, ArrowRight, Clock3 } from "lucide-react";
import { useTelegram } from "../hooks/useTelegram";
import { TrafficLights } from "../components/TrafficLights";
import { LandingContent } from "../components/landing/LandingContent";
import { EmptyState, ErrorState, LoadingState } from "../components/ui-states";
import { TrialStatusWidget } from "../components/TrialStatusWidget";
import {
  ConsumerHero,
  ConsumerMetaPill,
  ConsumerPageShell,
  ConsumerPanel,
  ConsumerStatusBadge,
} from "../components/consumer-page-shell";
import { HOME_FLOW_ID, HOME_MODULE_ID, ensureHomeCorrelation, homeFetch, makeHomeTrace, trackHomeEvent } from "../lib/home-analytics";

// START_MODULE_CONTRACT: M-HOME-FEED
// purpose: Render the home feed surface under strict GRACE with correlated telemetry and semantic feed blocks.
// owns:
//   - frontend/app/page.tsx
// inputs:
//   - Telegram runtime context, user profile, daily feed API, mock overrides
// outputs:
//   - Home feed hero, fallback and deeper CTA surfaces with correlated analytics
// dependencies:
//   - useTelegram, home analytics helper, MoonCard, TrafficLights, consumer page shell
// invariants:
//   - home telemetry uses flow_id=FLOW-HOME-FEED with surface=home
//   - feed states map to semantic blocks with data-testid wrappers
//   - CTA handlers and mock toggles emit correlated trace metadata
// failure_policy:
//   - API failures downgrade to fallback/empty/error surfaces without crashing the shell
// non_goals:
//   - week/catalog business logic beyond navigation and telemetry handoff
// END_MODULE_CONTRACT: M-HOME-FEED

// START_MODULE_MAP: M-HOME-FEED
// purpose: Map home feed entrypoints and trace obligations for strict GRACE.
// entrypoints:
//   - FeedPage
//   - FeedLayout
// contracts:
//   - FN-BOOTSTRAP-HOME-FEED
//   - FN-LOAD-HOME-FEED
//   - FN-HANDLE-HOME-CTA
//   - FN-HANDLE-HOME-MOCK-TOGGLE
// flow_id: HOME_FLOW_ID
// trace_obligations:
//   - every analytics/trace/log payload includes module, contract, block, semantic_block, correlation_id
//   - home surface telemetry includes surface=home, entry_point and block
// owned_tests:
//   - frontend/e2e/core-ux.spec.ts
//   - frontend/e2e/visual.spec.ts
// END_MODULE_MAP: M-HOME-FEED

type FeedState = "ready" | "fallback" | "empty";
type FeedLight = "green" | "yellow" | "red" | "gray";

type FastHitViewModel = { transit: string; natal: string; type: string; summary: string; orb?: number };
type FeedViewModel = {
  date: string;
  moon_sign: string;
  moon_phase: string;
  moon_emoji: string;
  general_vibe: string;
  traffic_lights: {
    health: FeedLight;
    money: FeedLight;
    love: FeedLight;
  };
  moon?: { sign?: string; phase?: string; emoji?: string };
  fast_hits?: FastHitViewModel[];
  personalization_level?: string | null;
  meta?: Record<string, unknown> | null;
};

type ProfileViewModel = {
  full_name?: string | null;
  birth_date?: string | null;
  subscription_active_until?: string | null;
  referral_code?: string | null;
};

type FeedSurfaceState = FeedState | "loading" | "error";
type MockFeedStateOverride = FeedState | "error" | undefined;
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
};

const DEFAULT_VIBE = "День лучше прожить в спокойном темпе: держитесь простых решений и не перегружайте себя лишним.";
const DEFAULT_LIGHTS: FeedViewModel["traffic_lights"] = {
  health: "gray",
  money: "gray",
  love: "gray",
};
const HOME_CONTRACTS = {
  bootstrap: "FN-BOOTSTRAP-HOME-FEED",
  load: "FN-LOAD-HOME-FEED",
  cta: "FN-HANDLE-HOME-CTA",
  mockToggle: "FN-HANDLE-HOME-MOCK-TOGGLE",
} as const;

type DayMode = "push" | "balance" | "caution" | "deep_focus" | "recovery";

type WindowTone = "best" | "soft" | "caution";

type ActionPlanItem = { id: string; label: string; text: string };

type ActionPlan = { actions: ActionPlanItem[]; risks: ActionPlanItem[] };

type TimelineWindow = { id: string; label: string; detail: string; tone: WindowTone };

type ExplainabilityChip = { id: string; label: string; detail: string };

const DAY_MODE_COPY: Record<
  DayMode,
  { label: string; description: string; badgeClass: string }
> = {
  push: {
    label: "День для рывка",
    description: "Можно продавливать подготовленные задачи, если не дробить внимание.",
    badgeClass: "border border-emerald-200 bg-emerald-50 text-emerald-900",
  },
  balance: {
    label: "День в балансе",
    description: "Держите темп короткими циклами и проверяйте стыки перед разворотом.",
    badgeClass: "border border-amber-200 bg-amber-50 text-amber-900",
  },
  caution: {
    label: "Осторожный день",
    description: "Лучше снять скорость и закреплять договорённости небольшими шагами.",
    badgeClass: "border border-rose-200 bg-rose-50 text-rose-900",
  },
  deep_focus: {
    label: "Глубокий фокус",
    description: "Сфокусируйтесь на одном важном блоке и уберите шум вокруг.",
    badgeClass: "border border-indigo-200 bg-indigo-50 text-indigo-900",
  },
  recovery: {
    label: "День на восстановление",
    description: "Сначала возвращаем ресурс тела и внимания, затем усиливаем ход.",
    badgeClass: "border border-slate-200 bg-slate-50 text-slate-800",
  },
};

const WINDOW_TONE_COPY: Record<
  WindowTone,
  { label: string; className: string }
> = {
  best: {
    label: "Лучшее окно",
    className: "border-emerald-100 bg-emerald-50",
  },
  soft: {
    label: "Мягкое окно",
    className: "border-amber-100 bg-amber-50",
  },
  caution: {
    label: "С осторожностью",
    className: "border-rose-100 bg-rose-50",
  },
};

const DOMAIN_ACTION_COPY = {
  health: {
    label: "Тонус и ресурс",
    green: "Поддержите тело движением, но через комфортный ритм.",
    yellow: "Сократите перегруз, добавьте паузы и воду.",
    red: "Сначала восстановитесь, потом планируйте рывок.",
  },
  money: {
    label: "Деньги и работа",
    green: "Смело фиксируйте договорённости и продвигайте сделки.",
    yellow: "Держите буфер по срокам и перепроверяйте цифры перед финалом.",
    red: "Не подписывайте резкие решения — вернитесь к обсуждению позже.",
  },
  love: {
    label: "Отношения и контакт",
    green: "Говорите прямо и поддержите тёплый контакт — это усиливает день.",
    yellow: "Уточняйте ожидания и не разгоняйте переписку шире сути.",
    red: "Поставьте разговор на паузу и сфокусируйтесь на фактах, не эмоциях.",
  },
} as const;

const buildMockProfile = (): ProfileViewModel => ({
  full_name: "Debug User",
  birth_date: "2000-01-01",
  subscription_active_until: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
  referral_code: "DEBUG123",
});

const buildMockFeed = (): FeedViewModel => ({
  date: "Сегодня",
  moon_sign: "Овен",
  moon_phase: "Растущая Луна",
  moon_emoji: "🌙",
  general_vibe: "Фокус на рутине и стабильных шагах.",
  traffic_lights: { health: "green", money: "yellow", love: "red" },
  moon: { sign: "Овен", phase: "Растущая Луна", emoji: "🌙" },
  fast_hits: [{ transit: "Venus", natal: "Venus", type: "Соединение", summary: "Венера соединение Венера" }],
  personalization_level: "personalized_v2",
  meta: { cache_scope: "mock-scope", personalization_level: "personalized_v2" },
});

const buildFallbackFeed = (): FeedViewModel => ({
  date: "Сегодня",
  moon_sign: "Не определён",
  moon_phase: "Фоновый режим",
  moon_emoji: "🌙",
  general_vibe: DEFAULT_VIBE,
  traffic_lights: DEFAULT_LIGHTS,
  moon: { sign: "Не определён", phase: "Фоновый режим", emoji: "🌙" },
  fast_hits: [],
  personalization_level: "fallback",
  meta: { fallback: true },
});

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
  if (!payload || typeof payload !== "object") {
    return buildMockProfile();
  }
  return { ...buildMockProfile(), ...normalizeProfile(payload) };
}

function normalizeFeed(payload: unknown): FeedViewModel | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const data = payload as Record<string, unknown>;
  const traffic = (data.traffic_lights && typeof data.traffic_lights === "object" ? data.traffic_lights : {}) as Record<string, unknown>;
  const moon = (data.moon && typeof data.moon === "object" ? data.moon : {}) as Record<string, unknown>;
  const fastHits = Array.isArray(data.fast_hits)
    ? data.fast_hits
        .filter((item): item is Record<string, unknown> => Boolean(item && typeof item === "object"))
        .map((item) => ({
          transit: typeof item.transit === "string" ? item.transit : "",
          natal: typeof item.natal === "string" ? item.natal : "",
          type: typeof item.type === "string" ? item.type : "",
          summary: typeof item.summary === "string" ? item.summary : "",
          orb: typeof item.orb === "number" ? item.orb : undefined,
        }))
    : [];

  return {
    date: typeof data.date === "string" ? data.date : "Сегодня",
    moon_sign: typeof data.moon_sign === "string" ? data.moon_sign : typeof moon.sign === "string" ? moon.sign : "Не определён",
    moon_phase: typeof data.moon_phase === "string" ? data.moon_phase : typeof moon.phase === "string" ? moon.phase : "Фоновый режим",
    moon_emoji: typeof data.moon_emoji === "string" ? data.moon_emoji : typeof moon.emoji === "string" ? moon.emoji : "🌙",
    general_vibe: typeof data.general_vibe === "string" ? data.general_vibe : DEFAULT_VIBE,
    traffic_lights: {
      health: isFeedLight(traffic.health) ? traffic.health : DEFAULT_LIGHTS.health,
      money: isFeedLight(traffic.money) ? traffic.money : DEFAULT_LIGHTS.money,
      love: isFeedLight(traffic.love) ? traffic.love : DEFAULT_LIGHTS.love,
    },
    moon: {
      sign: typeof moon.sign === "string" ? moon.sign : undefined,
      phase: typeof moon.phase === "string" ? moon.phase : undefined,
      emoji: typeof moon.emoji === "string" ? moon.emoji : undefined,
    },
    fast_hits: fastHits,
    personalization_level: typeof data.personalization_level === "string" ? data.personalization_level : null,
    meta: data.meta && typeof data.meta === "object" ? (data.meta as Record<string, unknown>) : null,
  };
}

function resolveDayMode(lights?: FeedViewModel["traffic_lights"], personalizationLevel?: string | null): DayMode {
  const statuses: FeedLight[] = [lights?.health, lights?.money, lights?.love].filter((value): value is FeedLight => Boolean(value));
  const redCount = statuses.filter((status) => status === "red").length;
  const yellowCount = statuses.filter((status) => status === "yellow").length;
  const greenCount = statuses.filter((status) => status === "green").length;

  if (lights?.health === "red") {
    return "recovery";
  }
  if (redCount >= 1) {
    return "caution";
  }
  if (greenCount >= 2) {
    return "push";
  }
  if (yellowCount >= 2) {
    return "balance";
  }
  return personalizationLevel === "personalized_v2" ? "deep_focus" : "balance";
}

function resolveWindowTone(hit: FastHitViewModel): WindowTone {
  const type = (hit.type || "").toLowerCase();
  const summary = (hit.summary || "").toLowerCase();
  const text = `${type} ${summary}`;
  if (text.includes("квадрат") || text.includes("square") || text.includes("оппоз")) {
    return "caution";
  }
  if (text.includes("трин") || text.includes("sext") || text.includes("сексти") || text.includes("trine")) {
    return "best";
  }
  return "soft";
}

function buildTimelineWindows(fastHits?: FastHitViewModel[] | null): TimelineWindow[] {
  if (!fastHits || !Array.isArray(fastHits)) {
    return [];
  }

  return fastHits
    .filter((hit) => typeof hit.summary === "string" && hit.summary.trim().length > 0)
    .slice(0, 4)
    .map((hit, index) => ({
      id: `${hit.summary}-${index}`,
      label: hit.summary.trim(),
      detail: hit.natal && hit.transit
        ? `${hit.transit} → ${hit.natal}`
        : hit.transit || hit.natal || "Личный фактор",
      tone: resolveWindowTone(hit),
    }));
}

function buildActionPlan(lights: FeedViewModel["traffic_lights"], vibe: string): ActionPlan {
  const actions: ActionPlanItem[] = [];
  const risks: ActionPlanItem[] = [];

  (Object.keys(DOMAIN_ACTION_COPY) as Array<keyof typeof DOMAIN_ACTION_COPY>).forEach((domainKey) => {
    const status = lights?.[domainKey as keyof FeedViewModel["traffic_lights"]] ?? "gray";
    const copy = DOMAIN_ACTION_COPY[domainKey];

    if (status === "green") {
      actions.push({ id: `${domainKey}-focus`, label: copy.label, text: copy.green });
      return;
    }
    if (status === "yellow") {
      risks.push({ id: `${domainKey}-yellow`, label: copy.label, text: copy.yellow });
      return;
    }
    if (status === "red") {
      risks.push({ id: `${domainKey}-red`, label: copy.label, text: copy.red });
    }
  });

  if (!actions.length) {
    actions.push({ id: "general-action", label: "Общий фон", text: vibe });
  }
  if (!risks.length) {
    risks.push({
      id: "general-risk",
      label: "Риск дня",
      text: "Не форсируйте решения быстрее готовности контекста.",
    });
  }

  return { actions, risks };
}

function buildExplainabilityChips(feed: FeedViewModel): ExplainabilityChip[] {
  const chips: ExplainabilityChip[] = [];
  const meta = feed.meta as (Record<string, unknown> & { fact_lines?: unknown }) | null;
  const rawFactLines = Array.isArray(meta?.fact_lines) ? (meta?.fact_lines as unknown[]) : [];

  rawFactLines
    .filter((item): item is string => typeof item === "string" && item.trim().length > 0)
    .slice(0, 3)
    .forEach((line, index) => {
      chips.push({ id: `fact-${index}`, label: `Фактор ${index + 1}`, detail: line.trim() });
    });

  if (!chips.length && Array.isArray(feed.fast_hits)) {
    feed.fast_hits
      .filter((hit) => typeof hit.summary === "string" && hit.summary.trim().length > 0)
      .slice(0, 2)
      .forEach((hit, index) => {
        chips.push({
          id: `hit-${index}`,
          label: hit.transit ? hit.transit : `Аспект ${index + 1}`,
          detail: hit.summary.trim(),
        });
      });
  }

  if (!chips.length) {
    chips.push({
      id: "moon",
      label: "Лунный фон",
      detail: `Луна в ${feed.moon?.sign || feed.moon_sign} — ${feed.moon?.phase || feed.moon_phase}`,
    });
  }

  return chips.slice(0, 3);
}

function resolveMockFeedState(mockState: MockFeedStateOverride, mockFeed: unknown) {
  const normalizedFeed = normalizeFeed(mockFeed) ?? buildMockFeed();

  switch (mockState) {
    case "fallback":
      return { nextFeed: buildFallbackFeed(), nextFeedState: "fallback" as FeedState, nextError: null };
    case "empty":
      return { nextFeed: null, nextFeedState: "empty" as FeedState, nextError: null };
    case "error":
      return { nextFeed: null, nextFeedState: "empty" as FeedState, nextError: "Не удалось загрузить астросводку" };
    default:
      return { nextFeed: normalizedFeed, nextFeedState: "ready" as FeedState, nextError: null };
  }
}

function isFeedLight(value: unknown): value is FeedLight {
  return value === "green" || value === "yellow" || value === "red" || value === "gray";
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

function formatSubscriptionLabel(dateValue?: string | null) {
  if (!dateValue) {
    return "Нет активной подписки";
  }

  const parsed = new Date(dateValue);
  if (Number.isNaN(parsed.getTime())) {
    return "Подписка активна";
  }

  return `Активна до ${parsed.toLocaleDateString("ru-RU", { day: "2-digit", month: "long" })}`;
}

function TodayVerdictCard({ feed }: { feed: FeedViewModel }) {
  const dayMode = resolveDayMode(feed.traffic_lights, feed.personalization_level);
  const dayModeCopy = DAY_MODE_COPY[dayMode];
  const moonSign = feed.moon?.sign || feed.moon_sign;
  const moonPhase = feed.moon?.phase || feed.moon_phase;
  const moonEmoji = feed.moon?.emoji || feed.moon_emoji;
  const fastHints = (feed.fast_hits ?? []).filter((hit) => hit.summary.trim().length > 0).slice(0, 2);

  return (
    <section data-testid="today-verdict" className="relative overflow-hidden rounded-[32px] border border-indigo-100 bg-[linear-gradient(145deg,#0f172a_0%,#1e1b4b_55%,#312e81_100%)] p-6 text-white shadow-[0_30px_70px_-45px_rgba(15,23,42,0.85)]">
      <div className="pointer-events-none absolute -left-16 top-6 h-48 w-48 rounded-full bg-amber-300/20 blur-3xl" />
      <div className="pointer-events-none absolute -right-20 bottom-0 h-60 w-60 rounded-full bg-fuchsia-500/20 blur-3xl" />
      <div className="relative z-10 flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-indigo-200">Вердикт дня</p>
          <div data-testid="today-day-mode" className={`mt-3 inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-semibold ${dayModeCopy.badgeClass}`}>
            {dayModeCopy.label}
          </div>
          <p className="mt-3 text-sm leading-relaxed text-indigo-100/80">{dayModeCopy.description}</p>
          <p className="mt-5 text-base font-medium leading-relaxed text-white/90">{feed.general_vibe}</p>
        </div>
        <div className="rounded-[24px] border border-white/20 bg-white/10 p-4 text-center shadow-lg shadow-slate-950/20">
          <div className="text-4xl" aria-hidden>{moonEmoji}</div>
          <p className="mt-3 text-sm font-black text-white">{moonSign}</p>
          <p className="text-xs text-white/70">{moonPhase}</p>
        </div>
      </div>
      <div className="relative z-10 mt-5 grid gap-3 sm:grid-cols-2">
        {fastHints.length ? (
          fastHints.map((hit, index) => (
            <article key={`${hit.summary}-${index}`} className="rounded-[20px] border border-white/20 bg-white/10 p-4 backdrop-blur">
              <p className="text-[11px] font-black uppercase tracking-[0.18em] text-indigo-100/70">
                {hit.transit || "Транзит"} • {hit.type || "Аспект"}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-white/90">{hit.summary}</p>
            </article>
          ))
        ) : (
          <p className="rounded-[20px] border border-white/20 bg-white/5 p-4 text-sm leading-relaxed text-white/80">
            Если быстрых окон нет, держитесь общего ритма: светофор сфокусирует действие.
          </p>
        )}
      </div>
    </section>
  );
}

function TodayWindowsPanel({ fastHits }: { fastHits?: FastHitViewModel[] | null }) {
  const windows = buildTimelineWindows(fastHits);

  return (
    <ConsumerPanel data-testid="today-windows" className="p-5 sm:p-6">
      <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">
        <Clock3 size={18} className="text-indigo-500" />
        Временные окна
      </div>
      {windows.length ? (
        <ol className="mt-4 space-y-3">
          {windows.map((window) => (
            <li
              key={window.id}
              data-testid={`today-window-${window.tone}`}
              className={`rounded-[22px] border ${WINDOW_TONE_COPY[window.tone].className} p-4 shadow-sm`}
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-black text-slate-900">{window.label}</p>
                <span className="rounded-full bg-white/80 px-3 py-1 text-xs font-semibold text-slate-700">{WINDOW_TONE_COPY[window.tone].label}</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">{window.detail}</p>
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-4 text-sm leading-relaxed text-slate-500">Сегодня окна распределены ровнее обычного — ориентируйтесь на главный вердикт.</p>
      )}
    </ConsumerPanel>
  );
}

function TodayActionPlanPanel({ lights, vibe }: { lights: FeedViewModel["traffic_lights"]; vibe: string }) {
  const plan = buildActionPlan(lights, vibe);

  return (
    <ConsumerPanel data-testid="today-actions" className="p-5 sm:p-6">
      <div className="grid gap-6 sm:grid-cols-2">
        <div>
          <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.22em] text-emerald-500">
            <ArrowRight size={16} />
            Что делать
          </div>
          <ul className="mt-3 space-y-3">
            {plan.actions.map((item) => (
              <li key={item.id} data-testid="today-action-item" className="rounded-[20px] border border-emerald-100 bg-emerald-50/60 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-emerald-800">{item.label}</p>
                <p className="mt-2 text-sm text-emerald-900/90">{item.text}</p>
              </li>
            ))}
          </ul>
        </div>
        <div data-testid="today-risks">
          <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.22em] text-rose-500">
            <AlertTriangle size={16} />
            Чего избегать
          </div>
          <ul className="mt-3 space-y-3">
            {plan.risks.map((item) => (
              <li key={item.id} className="rounded-[20px] border border-rose-100 bg-rose-50/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-rose-800">{item.label}</p>
                <p className="mt-2 text-sm text-rose-900/90">{item.text}</p>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </ConsumerPanel>
  );
}

function TodayExplainabilityPanel({ feed }: { feed: FeedViewModel }) {
  const chips = buildExplainabilityChips(feed);
  const personalMode = feed.personalization_level === "personalized_v2";

  return (
    <ConsumerPanel data-testid="today-explainability" className="p-5 sm:p-6">
      <div className="flex flex-wrap gap-2">
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
          {personalMode ? "Высокая уверенность" : "Бережный режим"}
        </span>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
          {personalMode ? "Точное время учтено" : "Без точного времени"}
        </span>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
          {chips.length} факторов
        </span>
      </div>
      <div className="mt-4 flex flex-wrap gap-3">
        {chips.map((chip) => (
          <article key={chip.id} data-testid="today-explainability-chip" className="rounded-[20px] border border-indigo-100 bg-indigo-50/70 p-4 text-slate-900">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-600">{chip.label}</p>
            <p className="mt-2 text-sm leading-relaxed text-slate-700">{chip.detail}</p>
          </article>
        ))}
      </div>
    </ConsumerPanel>
  );
}

function TodayCtaPanel({ onCta }: { onCta: (ctaId: string, href: string, entryPoint: string, block: string) => void }) {
  return (
    <ConsumerPanel data-testid="today-cta-panel" className="p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Следующий шаг</p>
          <h2 className="mt-2 text-lg font-black tracking-tight text-slate-900">Закрепите день неделей или отчётом</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-500">
            Неделя даёт карту на семь дней, а платёжный сценарий в каталоге открывает нужный разбор под задачу.
          </p>
        </div>
        <div className="grid gap-2 sm:min-w-[260px]">
          <Link
            href="/week"
            onClick={() => onCta("today-open-week", "/week", "today-cta", "DAY_CTA")}
            data-testid="today-cta-week"
            className="inline-flex items-center justify-center gap-2 rounded-full bg-slate-900 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-slate-200"
          >
            Неделя
            <ArrowRight size={16} />
          </Link>
          <Link
            href="/prices"
            onClick={() => onCta("today-open-premium", "/prices", "today-cta", "DAY_CTA")}
            data-testid="today-cta-premium"
            className="inline-flex items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700"
          >
            Продлить доступ
          </Link>
        </div>
      </div>
    </ConsumerPanel>
  );
}

function FeedLayout({ children, profile, state, dateLabel }: FeedLayoutProps) {
  const dateMeta = dateLabel || "Сегодня";

  return (
    <ConsumerPageShell testId="home-feed-page">
      <section className="space-y-4" data-testid="home-feed-shell">
        <ConsumerHero
          eyebrow="Сегодня"
          title="Главный сценарий дня"
          description="Вердикт, окна и действия/риски собраны в одном экране, чтобы быстро понять как вести день."
          status={
            <ConsumerStatusBadge
              label={state === "ready" ? "Прогноз готов" : state === "fallback" ? "Бережный режим" : state === "loading" ? "Загружаем" : "Нужен повтор"}
              description={profile?.full_name || "Персональная сводка"}
              tone={state === "ready" ? "emerald" : state === "fallback" ? "amber" : state === "error" ? "rose" : "indigo"}
            />
          }
          meta={
            <>
              <ConsumerMetaPill label="Дата" value={dateMeta} />
              <ConsumerMetaPill label="Формат" value="Вердикт • Окна • CTA" />
              <ConsumerMetaPill label="Подписка" value={formatSubscriptionLabel(profile?.subscription_active_until)} />
            </>
          }
        />
        {children}
      </section>
    </ConsumerPageShell>
  );
}

export default function FeedPage() {
  const { user, initData, isReady, mode } = useTelegram();
  const router = useRouter();
  const [feed, setFeed] = useState<FeedViewModel | null>(null);
  const [profile, setProfile] = useState<ProfileViewModel | null>(null);
  const [feedState, setFeedState] = useState<FeedState>("ready");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const correlationId = useMemo(() => ensureHomeCorrelation(), []);
  const shouldShowLanding = !loading && (mode === "guest" || mode === "none" || !user || !initData);

  const emitHomeEvent = useCallback(
    (eventName: string, block: string, semanticBlock: string, meta: Record<string, unknown> = {}) =>
      trackHomeEvent(
        eventName,
        {
          ...makeHomeTrace({
            contract: HOME_CONTRACTS.load,
            block,
            semantic_block: semanticBlock,
            correlation_id: correlationId,
          }),
          entry_point: typeof meta.entry_point === "string" ? meta.entry_point : "home-feed",
          ...meta,
        },
        { correlationId, flowId: HOME_FLOW_ID, block },
      ),
    [correlationId],
  );

  const loadFeedPage = useCallback(async () => {
    if (!user || !initData) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    await emitHomeEvent("home.feed_load_started", "FEED_BOOTSTRAP", "FEED_BOOTSTRAP", {
      contract: HOME_CONTRACTS.load,
      entry_point: mode === "mock" ? "home-feed-mock" : "home-feed-live",
      status: "started",
      user_id: user.id,
    });

    try {
      const [profileResult, feedResult] = await Promise.allSettled([
        fetchJson("/api/users/me", { headers: { "X-Telegram-Auth": initData } }, "FEED_BOOTSTRAP"),
        fetchJson(`/api/feed/today${mode === "mock" ? "?debug=true" : ""}`, {
          headers: mode === "mock"
            ? { "X-Telegram-Auth": initData, "X-Feed-Debug": "1" }
            : { "X-Telegram-Auth": initData },
        }, "FEED_BOOTSTRAP"),
      ]);

      if (profileResult.status !== "fulfilled") {
        throw new Error(toErrorMessage(profileResult.reason, "Не удалось загрузить профиль"));
      }

      const nextProfile = normalizeProfile(profileResult.value);
      setProfile(nextProfile);

      if (!nextProfile.birth_date) {
        await emitHomeEvent("home.feed_profile_redirect", "FEED_BOOTSTRAP", "FEED_BOOTSTRAP", {
          contract: HOME_CONTRACTS.load,
          status: "redirect",
          entry_point: "home-feed-profile-guard",
          target: "/onboarding/profile",
        });
        router.push("/onboarding/profile");
        return;
      }

      if (feedResult.status === "fulfilled") {
        const nextFeed = normalizeFeed(feedResult.value);
        if (nextFeed) {
          setFeed(nextFeed);
          setFeedState("ready");
          await emitHomeEvent("home.feed_load_success", "FEED_LOAD_SUCCESS", "FEED_LOAD_SUCCESS", {
            contract: HOME_CONTRACTS.load,
            status: "success",
            entry_point: "home-feed-api",
            personalization_level: nextFeed.personalization_level,
          });
        } else {
          setFeed(null);
          setFeedState("empty");
          await emitHomeEvent("home.feed_load_empty", "FEED_LOAD_EMPTY", "FEED_LOAD_EMPTY", {
            contract: HOME_CONTRACTS.load,
            status: "empty",
            entry_point: "home-feed-api",
          });
        }
      } else {
        setFeed(buildFallbackFeed());
        setFeedState("fallback");
        await emitHomeEvent("home.feed_load_fallback", "FEED_LOAD_FALLBACK", "FEED_LOAD_FALLBACK", {
          contract: HOME_CONTRACTS.load,
          status: "fallback",
          entry_point: "home-feed-api",
          message: toErrorMessage(feedResult.reason, "fallback"),
        });
      }
    } catch (err) {
      setProfile(null);
      setFeed(null);
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
  }, [emitHomeEvent, initData, mode, router, user]);

  useEffect(() => {
    if (!isReady) {
      return;
    }

    void trackHomeEvent(
      "home.feed_bootstrap",
      {
        ...makeHomeTrace({
          contract: HOME_CONTRACTS.bootstrap,
          block: "FEED_BOOTSTRAP",
          semantic_block: "FEED_BOOTSTRAP",
          correlation_id: correlationId,
        }),
        entry_point: "home-surface-init",
        mode,
        ready: isReady,
        user_id: user?.id,
      },
      { correlationId, flowId: HOME_FLOW_ID, block: "FEED_BOOTSTRAP" },
    );

    if (mode === "mock") {
      const mockWindow = window as MockWindow;
      const nextProfile = normalizeMockProfile(mockWindow.MOCK_PROFILE_OVERRIDE);
      const { nextFeed, nextFeedState, nextError } = resolveMockFeedState(
        mockWindow.MOCK_FEED_STATE,
        mockWindow.MOCK_FEED_OVERRIDE,
      );

      setProfile(nextProfile);
      setFeed(nextFeed);
      setFeedState(nextFeedState);
      setError(nextError);
      setLoading(false);
      void trackHomeEvent(
        "home.feed_mock_state",
        {
          ...makeHomeTrace({
            contract: HOME_CONTRACTS.mockToggle,
            block: "FEED_BOOTSTRAP",
            semantic_block: "FEED_BOOTSTRAP",
            correlation_id: correlationId,
          }),
          entry_point: "home-feed-mock-toggle",
          status: nextError ? "error" : nextFeedState,
          mock_feed_state: nextFeedState,
        },
        { correlationId, flowId: HOME_FLOW_ID, block: "FEED_BOOTSTRAP" },
      );
      return;
    }

    if (mode === "telegram" && user && initData) {
      void loadFeedPage();
      return;
    }

    if (mode === "guest" || mode === "none" || !user || !initData) {
      setLoading(false);
      return;
    }

    void loadFeedPage();
  }, [correlationId, initData, isReady, loadFeedPage, mode, user]);

  const handleHomeCta = useCallback(
    (ctaId: string, href: string, entryPoint: string, block: string) => {
      void trackHomeEvent(
        "home.feed_cta_click",
        {
          ...makeHomeTrace({
            contract: HOME_CONTRACTS.cta,
            block,
            semantic_block: block,
            correlation_id: correlationId,
          }),
          entry_point: entryPoint,
          cta_id: ctaId,
          href,
          status: "click",
        },
        { correlationId, flowId: HOME_FLOW_ID, block },
      );
    },
    [correlationId],
  );

  if (!isReady || loading) {
    return (
    <FeedLayout state="loading" profile={profile}>
        <ConsumerPanel className="p-5">
          <LoadingState compact message="Собираем домашний экран..." />
        </ConsumerPanel>
      </FeedLayout>
    );
  }

  if (shouldShowLanding) {
    return <LandingContent />;
  }

  if (error) {
    return (
    <FeedLayout state="error" profile={profile}>
        <ConsumerPanel className="p-5">
          <ErrorState compact error={error} />
        </ConsumerPanel>
      </FeedLayout>
    );
  }

  if (!feed) {
    return (
    <FeedLayout state={feedState} profile={profile}>
        <ConsumerPanel className="p-5">
          <EmptyState
            compact
            title="Лента пока пуста"
            message="Когда персональная сводка станет доступна, здесь появятся луна, аспекты и недельный светофор."
            actionLabel="Открыть каталог"
            actionHref="/create"
          />
        </ConsumerPanel>
      </FeedLayout>
    );
  }

  return (
    <FeedLayout state={feedState} profile={profile} dateLabel={feed.date}>
      <div className="space-y-4">
        <TodayVerdictCard feed={feed} />

        <TrafficLights lights={feed.traffic_lights} personalizationLevel={feed.personalization_level} />

        <TodayWindowsPanel fastHits={feed.fast_hits} />

        <TodayActionPlanPanel lights={feed.traffic_lights} vibe={feed.general_vibe} />

        <TodayExplainabilityPanel feed={feed} />

        <TodayCtaPanel onCta={handleHomeCta} />

        {profile ? <TrialStatusWidget activeUntil={profile.subscription_active_until ?? null} referralCode={profile.referral_code ?? null} /> : null}
      </div>
    </FeedLayout>
  );
}
