"use client";

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useSearchParams } from "next/navigation";

import { useTelegram } from "../../hooks/useTelegram";
import { CatalogCheckoutResumeBanner } from "../../components/catalog/catalog-checkout-resume";
import {
  FLOW_FORECAST_CATALOG,
  setCatalogAnalyticsContext,
  startCatalogCorrelation,
  trackCatalogEvent,
} from "../../components/catalog/catalog-analytics";
import { CorrelationManager, correlatedFetch } from "../../lib/correlation";
import { ConsumerPageShell, ConsumerPanel, ConsumerStatusBadge } from "../../components/consumer-page-shell";
import { EmptyState, ErrorState, LoadingState } from "../../components/ui-states";
import { WeekHeroMap } from "../../components/week/week-hero-map";
import { WeekDayStrip } from "../../components/week/week-day-strip";
import { WeekDayGrid } from "../../components/week/week-day-grid";
import { WeekDomainPanel } from "../../components/week/week-domain-panel";
import { WeekActionsPanel } from "../../components/week/week-actions-panel";
import { WeekExplainabilityPanel } from "../../components/week/week-explainability-panel";
import { WeekDeepSections } from "../../components/week/week-deep-sections";
import ReportStatusPoller from "../../components/report-status-poller";
import {
  confidenceBucket,
  hasExplicitWeekCompatibilityPayload,
  mapCanonicalWeekBriefToSurface,
  mapLegacyWeekFallbackToSurface,
  type WeekBrief,
  type LegacyWeekMapPayload,
} from "../../lib/week-brief";

type WeekReportSummary = {
  id?: string;
  report_type?: string;
  status?: string;
  created_at?: string;
};

type WeekReportPayload = {
  report?: { id?: string; report_type?: string; status?: string } | null;
  week_brief?: WeekBrief | null;
  week_brief_envelope?: { status?: string; data?: WeekBrief | null; message?: string | null } | null;
  week_map?: LegacyWeekMapPayload | null;
  chunks?: { id?: string; section?: string; title?: string; content?: unknown }[] | null;
  timezone?: string | null;
  location?: string | null;
};

type WeekEmptyStateCopy = {
  primaryLabel: string;
  primaryHref: string;
  note: string;
};

type MockWeekWindow = Window & {
  MOCK_WEEK_MAP_OVERRIDE?: LegacyWeekMapPayload;
  MOCK_WEEK_BRIEF_OVERRIDE?: WeekBrief;
};

function parseReportCreatedAt(value?: string): number {
  if (!value) return Number.NEGATIVE_INFINITY;
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : Number.NEGATIVE_INFINITY;
}

function resolveWeekEmptyStateCopy(latestReportMeta: WeekReportSummary | null): WeekEmptyStateCopy {
  if (latestReportMeta?.status === "in_progress") {
    return {
      primaryLabel: "Открыть собирающийся отчёт",
      primaryHref: latestReportMeta.id ? `/read/${latestReportMeta.id}` : "/reports/history",
      note: "Персональный weekly report ещё собирается. Полный экран недели появится после завершения генерации.",
    };
  }

  return {
    primaryLabel: "Собрать персональную неделю",
    primaryHref: "/create?type=week_forecast",
    note: "Для этого Telegram-профиля ещё нет сохранённого weekly report в истории. Чтобы увидеть персональную неделю, соберите новый отчёт.",
  };
}

// START_MODULE_CONTRACT: M-WEEK-PAGE
// purpose: Render the personalized week surface with correlated fetch, fallback handling, and strict-GRACE semantic blocks.
// owns:
//   - frontend/app/week/page.tsx
// inputs:
//   - Telegram auth context, latest week report metadata, week report payload
// outputs:
//   - week page states, telemetry events, resume/banner handoff, report-status polling
// dependencies:
//   - ../../hooks/useTelegram
//   - ../../components/catalog/catalog-analytics
//   - ../../lib/correlation
//   - ../../lib/week-brief
// invariants:
//   - week telemetry uses flow_id=FLOW_FORECAST_CATALOG with surface=week
//   - page state transitions stay inside explicit semantic blocks
//   - payload shaping is delegated to canonical/degraded week mappers
// failure_policy:
//   - report lookup and payload fetch failures degrade to recoverable error or empty states without crashing the shell
// non_goals:
//   - changing week business copy or splitting the page controller in this wave
// END_MODULE_CONTRACT: M-WEEK-PAGE

// START_MODULE_MAP: M-WEEK-PAGE
// entrypoints:
//   - WeekPage
//   - WeekPageContent
// helpers:
//   - ensureCorrelationId
//   - logWeekError
//   - fetchLatestReport
//   - fetchWeekPayload
//   - initPage
//   - trackDayClick
// owned_tests:
//   - frontend/test/app/week-page.test.tsx
//   - frontend/test/components/week/week-detail-panels.test.tsx
//   - frontend/test/components/week-explainability-panel.test.tsx
// adjacent_modules:
//   - frontend/lib/week-brief.ts
//   - frontend/components/week/week-hero-map.tsx
//   - frontend/components/catalog/catalog-checkout-resume.tsx
// END_MODULE_MAP: M-WEEK-PAGE

const DEFAULT_WEEK_MAP: LegacyWeekMapPayload = {
  thesis: "Неделя просит точного темпа: двигайте главное и сразу фиксируйте результат.",
  theme: "Фокус через короткие циклы и аккуратный контроль деталей.",
  day_cards: [
    { weekday: "Понедельник", date: "2026-03-23", mode: "GREEN", headline: "Хороший день, чтобы собрать договорённости.", best_for: ["Планирование", "Переговоры"], avoid: ["Поспешные обещания"], score: 0.2 },
    { weekday: "Вторник", date: "2026-03-24", mode: "YELLOW", headline: "Темп рывками, проверяйте стыки.", best_for: ["Редактура", "Короткие встречи"], avoid: ["Конфликты"], score: 0.9 },
    { weekday: "Среда", date: "2026-03-25", mode: "RED", headline: "Не давите силой, оставьте буфер.", best_for: ["Рутина"], avoid: ["Срочные сделки"], score: 2.1 },
    { weekday: "Четверг", date: "2026-03-26", mode: "YELLOW", headline: "Возвращайтесь ко второму проходу.", best_for: ["Уточнения"], avoid: ["Споры"], score: 1.1 },
    { weekday: "Пятница", date: "2026-03-27", mode: "GREEN", headline: "Хорошо закреплять результат.", best_for: ["Презентации"], avoid: ["Избыточный контроль"], score: 0.3 },
    { weekday: "Суббота", date: "2026-03-28", mode: "YELLOW", headline: "Снижайте ритм и не распыляйтесь.", best_for: ["Быт", "Восстановление"], avoid: ["Перегруз"], score: 1.2 },
    { weekday: "Воскресенье", date: "2026-03-29", mode: "GREEN", headline: "Спокойно соберите следующую неделю.", best_for: ["План", "Отдых"], avoid: ["Суета"], score: 0.4 },
  ],
  domains: { work: 70, relationships: 60, energy: 58, focus: 65 },
  major_factors: [
    { label: "Тема недели", category: "period_theme", impact_pct: 42.5, explanation: "Фон удерживает курс на рабочие договорённости.", confidence: 0.81 },
    { label: "Окно результата", category: "timing", impact_pct: 24, explanation: "Лучше всего работают повторные проходы и точные договорённости.", confidence: 0.74 },
  ],
  actions: ["Закрывайте по одному важному решению за раз.", "Возвращайтесь ко второму проходу вместо силового рывка.", "Сверяйте ожидания в переговорах заранее."],
  risks: ["Не форсируйте то, что должно дозреть.", "Не распыляйтесь на параллельные обещания."],
  deep_sections: ["strategy", "domains", "timeline"],
  explainability: { confidence: 0.78, used_exact_birth_time: true },
  timezone: "Europe/Moscow",
  location: "Moscow",
  week_start: "2026-03-23",
};

// FN-CONTRACT: FN-WEEK-PAGE-CONTENT
// purpose: Coordinate week page loading, telemetry, and semantic rendering states.
// inputs: pathname, searchParams, Telegram runtime, report APIs
// outputs: rendered week shell or state surface
// invariants: correlated telemetry precedes async flows; week surface derives from normalized mapper only
function WeekPageContent() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { initData, isReady, mode } = useTelegram();
  const isMockHelperLane = mode === "mock";
  const isCanonicalTelegramLane = mode === "telegram" && Boolean(initData);
  const correlationIdRef = useRef<string>("");
  const viewTrackedRef = useRef(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [latestReportId, setLatestReportId] = useState<string | null>(null);
  const [latestReportStatus, setLatestReportStatus] = useState<string | null>(null);
  const [latestReportMeta, setLatestReportMeta] = useState<WeekReportSummary | null>(null);
  const [payload, setPayload] = useState<WeekReportPayload | null>(null);

  // FN-CONTRACT: FN-WEEK-ENSURE-CORRELATION
  // purpose: Ensure a stable correlation id for every week flow branch within one page lifecycle.
  const ensureCorrelationId = useCallback(() => {
    if (!correlationIdRef.current) {
      correlationIdRef.current = startCatalogCorrelation("week_page");
    }
    CorrelationManager.setCorrelationId(correlationIdRef.current);
    return correlationIdRef.current;
  }, []);

  const mockRuntime = isMockHelperLane && searchParams?.get("mock") === "1";
  const runtimeParam = searchParams?.get("runtime") === "1";
  const checkoutToken = searchParams?.get("checkout") ?? undefined;

  // FN-CONTRACT: FN-WEEK-LOG-ERROR
  // purpose: Record week-flow failures with stable block labels and mirror them into renderable state.
  const logWeekError = useCallback(
    (action: string, reason: unknown, block: string) => {
      const message = reason instanceof Error ? reason.message : typeof reason === "string" ? reason : "Unknown week error";
      void trackCatalogEvent(
        "week.error",
        {
          surface: "week",
          flow_id: FLOW_FORECAST_CATALOG,
          correlation_id: ensureCorrelationId(),
          action,
          reason: message,
          block,
        },
        { correlationId: ensureCorrelationId(), flowId: FLOW_FORECAST_CATALOG, block },
      );
      setError(message);
    },
    [ensureCorrelationId],
  );

  // FN-CONTRACT: FN-WEEK-FETCH-LATEST-REPORT
  // purpose: Resolve the latest relevant week report eligible for page hydration.
  const fetchLatestReport = useCallback(async () => {
    if (mockRuntime) {
      return {
        id: "mock-week-report",
        report_type: "week_forecast",
        status: "completed",
      } satisfies WeekReportSummary;
    }

    if ((!isCanonicalTelegramLane && !isMockHelperLane) || !initData) return null;
    const response = await correlatedFetch("/api/reports/my?limit=20", { headers: { "X-Telegram-Auth": initData } });
    if (!response.ok) throw new Error(`REPORT_LOOKUP_${response.status}`);
    const data = (await response.json()) as WeekReportSummary[];
    const latest = Array.isArray(data)
      ? data
          .filter((item) => item.report_type === "week_forecast" && (item.status === "completed" || item.status === "in_progress"))
          .sort((left, right) => parseReportCreatedAt(right.created_at) - parseReportCreatedAt(left.created_at))[0] ?? null
      : null;
    return latest ?? null;
  }, [initData, isCanonicalTelegramLane, isMockHelperLane, mockRuntime]);

  // FN-CONTRACT: FN-WEEK-FETCH-PAYLOAD
  // purpose: Fetch or mock the detailed week payload for a resolved report summary.
  const fetchWeekPayload = useCallback(async (report: WeekReportSummary | null) => {
    if (mockRuntime && typeof window !== "undefined") {
      const mockWindow = window as MockWeekWindow;
      return {
        report: { id: report?.id ?? "mock-week-report", report_type: "week_forecast", status: "completed" },
        week_map: mockWindow.MOCK_WEEK_MAP_OVERRIDE ?? null,
        week_brief: mockWindow.MOCK_WEEK_BRIEF_OVERRIDE ?? null,
        chunks: null,
      } satisfies WeekReportPayload;
    }

    const reportId = report?.id ?? null;
    if (!reportId || !initData) return null;
    const response = await correlatedFetch(`/api/reports/${reportId}`, { headers: { "X-Telegram-Auth": initData } });
    if (!response.ok) throw new Error(`FETCH_WEEK_${response.status}`);
    return (await response.json()) as WeekReportPayload;
  }, [initData, mockRuntime]);

  // FN-CONTRACT: FN-WEEK-INIT-PAGE
  // purpose: Bootstrap week analytics context, fetch latest report metadata, and hydrate payload state.
  const initPage = useCallback(async () => {
    if (!isReady) return;
    if (!isCanonicalTelegramLane && !isMockHelperLane) {
      setLoading(false);
      return;
    }

    // START_BLOCK: WEEK_INIT_FLOW
    setLoading(true);
    setError(null);
    ensureCorrelationId();
    setCatalogAnalyticsContext({ correlation_id: ensureCorrelationId(), flow_id: FLOW_FORECAST_CATALOG, surface: "week" });

    try {
      const reportMeta = await fetchLatestReport();
      setLatestReportMeta(reportMeta);
      setLatestReportId(reportMeta?.id ?? null);
      setLatestReportStatus(reportMeta?.status ?? null);
      const weekPayload = await fetchWeekPayload(reportMeta);
      setPayload(weekPayload);
    } catch (cause) {
      logWeekError("week_page_init", cause, "WEEK_INIT");
    } finally {
      setLoading(false);
    }
    // END_BLOCK: WEEK_INIT_FLOW
  }, [ensureCorrelationId, fetchLatestReport, fetchWeekPayload, isCanonicalTelegramLane, isMockHelperLane, isReady, logWeekError]);

  useEffect(() => {
    void initPage();
  }, [initPage, pathname]);

  // START_BLOCK: WEEK_SURFACE_MODEL
  const week = useMemo(() => {
    const canonicalWeekBrief = payload?.week_brief_envelope?.data ?? payload?.week_brief ?? null;
    if (canonicalWeekBrief) {
      return mapCanonicalWeekBriefToSurface({
        weekBrief: canonicalWeekBrief,
        latestReportId,
        sourceStatus: latestReportStatus,
      });
    }

    if (!hasExplicitWeekCompatibilityPayload({ legacyWeekMap: payload?.week_map ?? null, chunks: payload?.chunks ?? null })) {
      return null;
    }

    return mapLegacyWeekFallbackToSurface({
      legacyWeekMap: payload?.week_map ?? DEFAULT_WEEK_MAP,
      chunks: payload?.chunks ?? null,
      latestReportId,
      sourceStatus: latestReportStatus,
    });
  }, [latestReportId, latestReportStatus, payload]);
  // END_BLOCK: WEEK_SURFACE_MODEL

  useEffect(() => {
    // START_BLOCK: WEEK_VIEW_TELEMETRY
    if (loading || error || viewTrackedRef.current || !week) return;
    viewTrackedRef.current = true;
    void trackCatalogEvent(
      "week.brief_view",
      {
        surface: "week",
        flow_id: FLOW_FORECAST_CATALOG,
        correlation_id: ensureCorrelationId(),
        block: "WEEK_BRIEF_VIEW",
        week_type: week.weekType,
        confidence_bucket: confidenceBucket(week.explainability.confidence),
        birth_time_used: week.explainability.birth_time_used,
        status: week.status,
        sections_count: week.sectionsCount,
        personalization_level: week.personalizationLevel,
      },
      { correlationId: ensureCorrelationId(), flowId: FLOW_FORECAST_CATALOG, block: "WEEK_BRIEF_VIEW" },
    );
  }, [ensureCorrelationId, error, loading, week]);
  // END_BLOCK: WEEK_VIEW_TELEMETRY

  // FN-CONTRACT: FN-WEEK-TRACK-DAY-CLICK
  // purpose: Emit correlated analytics for week day-card interaction without mutating domain state.
  const trackDayClick = useCallback(
    (day: string) => {
      void trackCatalogEvent(
        "week.day_card_click",
        {
          surface: "week",
          flow_id: FLOW_FORECAST_CATALOG,
          correlation_id: ensureCorrelationId(),
          block: "WEEK_DAY_GRID",
          day,
          week_type: week?.weekType ?? "balance",
        },
        { correlationId: ensureCorrelationId(), flowId: FLOW_FORECAST_CATALOG, block: "WEEK_DAY_GRID" },
      );
    },
    [ensureCorrelationId, week?.weekType],
  );

  const primaryHref = week?.cta.primary?.href || (week?.reportId ? `/read/${week.reportId}` : "/create?type=week_forecast");
  const primaryLabel = week?.cta.primary?.label || (week?.reportId ? "Открыть полный отчёт" : "Получить полный отчёт");
  const emptyStateCopy = useMemo(() => resolveWeekEmptyStateCopy(latestReportMeta), [latestReportMeta]);

  // START_BLOCK: WEEK_RENDER_SWITCH
  if (!isReady || loading) {
    return (
      <ConsumerPageShell testId="week-page">
        <ConsumerPanel className="p-5">
          <LoadingState compact message="Сводим данные недели" />
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  if (!isCanonicalTelegramLane && !isMockHelperLane) {
    return (
      <ConsumerPageShell testId="week-page">
        <ConsumerPanel className="p-5">
          <EmptyState
            compact
            title="Неделя пока недоступна"
            message="Авторизуйтесь через Telegram, чтобы увидеть персональную карту недели."
            actionLabel="К историям отчётов"
            actionHref="/reports/history"
          />
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  if (error) {
    return (
      <ConsumerPageShell testId="week-page">
        <ConsumerPanel className="border-rose-100 p-5">
          <ErrorState compact error={error} onRetry={initPage} />
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  if (!week) {
    return (
      <ConsumerPageShell testId="week-page">
        <ConsumerPanel className="p-5">
          <EmptyState
            compact
            title={latestReportMeta?.status === "in_progress" ? "Персональная неделя ещё собирается" : "Персональной недели пока нет"}
            message={emptyStateCopy.note}
            actionLabel={emptyStateCopy.primaryLabel}
            actionHref={emptyStateCopy.primaryHref}
          />
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  const hasConcreteWeekReport = Boolean(week.reportId);
  const resolvedPrimaryHref = hasConcreteWeekReport ? primaryHref : emptyStateCopy.primaryHref;
  const resolvedPrimaryLabel = hasConcreteWeekReport ? primaryLabel : emptyStateCopy.primaryLabel;
  const shouldShowFallbackNote = week.surfaceMode === "compatibility";

  return (
    // START_BLOCK: WEEK_READY_SURFACE
    <ConsumerPageShell testId="week-page">
      <section className="space-y-4" data-testid="week-map-surface">
        <CatalogCheckoutResumeBanner
          checkoutToken={checkoutToken}
          initData={initData ?? ""}
          isReady={Boolean(isReady)}
          mode={mode ?? "none"}
          mockEnabled={mockRuntime}
          runtimeEnabled={runtimeParam}
          surface="week"
          entryPoint="week-resume-banner"
        />

        <WeekHeroMap
          week={week}
          primaryHref={resolvedPrimaryHref}
          primaryLabel={resolvedPrimaryLabel}
          onPrimaryClick={() => {
            void trackCatalogEvent(
              week.reportId ? "week.open_full_report_click" : "week.premium_click",
              {
                surface: "week",
                flow_id: FLOW_FORECAST_CATALOG,
                correlation_id: ensureCorrelationId(),
                block: "WEEK_PRIMARY_CTA",
                week_type: week.weekType,
                cta_href: resolvedPrimaryHref,
              },
              { correlationId: ensureCorrelationId(), flowId: FLOW_FORECAST_CATALOG, block: "WEEK_PRIMARY_CTA" },
            );
          }}
        />

        <WeekDayStrip week={week} onDayClick={trackDayClick} />
        <WeekDayGrid week={week} onDayClick={trackDayClick} />
        <WeekDomainPanel week={week} />
        <WeekActionsPanel week={week} />
        <WeekExplainabilityPanel week={week} />
        <WeekDeepSections week={week} />

        {shouldShowFallbackNote ? (
          <p className="text-xs text-slate-500" data-testid="week-fallback-note">
            {week.reportId ? "Показан совместимый fallback-режим: верхний слой WeekBrief недоступен, поэтому экран собран из legacy week_map." : emptyStateCopy.note}
          </p>
        ) : null}
      </section>
    </ConsumerPageShell>
  );
  // END_BLOCK: WEEK_READY_SURFACE
  // END_BLOCK: WEEK_RENDER_SWITCH
}

// FN-CONTRACT: FN-WEEK-PAGE
// purpose: Provide a suspense boundary for the week route and delegate all orchestration to `WeekPageContent`.
export default function WeekPage() {
  return (
    <Suspense fallback={<ConsumerPageShell testId="week-page"><ConsumerPanel className="p-5"><LoadingState compact message="Собираем карту недели..." /></ConsumerPanel></ConsumerPageShell>}>
      <WeekPageContent />
    </Suspense>
  );
}
