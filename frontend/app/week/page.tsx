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
import { WeekDayGrid } from "../../components/week/week-day-grid";
import { WeekDomainPanel } from "../../components/week/week-domain-panel";
import { WeekActionsPanel } from "../../components/week/week-actions-panel";
import { WeekExplainabilityPanel } from "../../components/week/week-explainability-panel";
import { WeekDeepSections } from "../../components/week/week-deep-sections";
import { confidenceBucket, mapWeekReportToWeekBrief, type WeekBrief, type LegacyWeekMapPayload } from "../../lib/week-brief";

type WeekReportSummary = {
  id?: string;
  report_type?: string;
  status?: string;
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

type MockWeekWindow = Window & {
  MOCK_WEEK_MAP_OVERRIDE?: LegacyWeekMapPayload;
  MOCK_WEEK_BRIEF_OVERRIDE?: WeekBrief;
};

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

function WeekPageContent() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { initData, isReady, mode } = useTelegram();
  const correlationIdRef = useRef<string>("");
  const viewTrackedRef = useRef(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [latestReportId, setLatestReportId] = useState<string | null>(null);
  const [payload, setPayload] = useState<WeekReportPayload | null>(null);

  const ensureCorrelationId = useCallback(() => {
    if (!correlationIdRef.current) {
      correlationIdRef.current = startCatalogCorrelation("week_page");
    }
    CorrelationManager.setCorrelationId(correlationIdRef.current);
    return correlationIdRef.current;
  }, []);

  const mockRuntime = searchParams?.get("mock") === "1";
  const runtimeParam = searchParams?.get("runtime") === "1";
  const checkoutToken = searchParams?.get("checkout") ?? undefined;

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

  const fetchLatestReport = useCallback(async () => {
    if (mode === "guest" || mode === "none" || !initData) return null;
    const response = await correlatedFetch("/api/reports/my?limit=20", { headers: { "X-Telegram-Auth": initData } });
    if (!response.ok) throw new Error(`REPORT_LOOKUP_${response.status}`);
    const data = (await response.json()) as WeekReportSummary[];
    const latest = Array.isArray(data)
      ? data.find((item) => item.report_type === "week_forecast" && item.status === "completed")
      : null;
    return latest?.id ?? null;
  }, [initData, mode]);

  const fetchWeekPayload = useCallback(async (reportId: string | null) => {
    if (mockRuntime && typeof window !== "undefined") {
      const mockWindow = window as MockWeekWindow;
      return {
        report: { id: reportId ?? "mock-week-report", report_type: "week_forecast", status: "completed" },
        week_map: mockWindow.MOCK_WEEK_MAP_OVERRIDE ?? DEFAULT_WEEK_MAP,
        week_brief: mockWindow.MOCK_WEEK_BRIEF_OVERRIDE ?? null,
        chunks: [
          {
            id: "week-strategy",
            section: "week_strategy",
            title: "Стратегия недели",
            content: "Неделя лучше проходит через короткие циклы, а не через силовой рывок.",
          },
        ],
      } satisfies WeekReportPayload;
    }

    if (!reportId || !initData) return null;
    const response = await correlatedFetch(`/api/reports/${reportId}`, { headers: { "X-Telegram-Auth": initData } });
    if (!response.ok) throw new Error(`FETCH_WEEK_${response.status}`);
    return (await response.json()) as WeekReportPayload;
  }, [initData, mockRuntime]);

  const initPage = useCallback(async () => {
    if (!isReady) return;
    if (mode === "guest" || mode === "none" || !initData) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    ensureCorrelationId();
    setCatalogAnalyticsContext({ correlationId: ensureCorrelationId(), flowId: FLOW_FORECAST_CATALOG, surface: "week" });

    try {
      const reportId = await fetchLatestReport();
      setLatestReportId(reportId);
      const weekPayload = await fetchWeekPayload(reportId);
      setPayload(weekPayload);
    } catch (cause) {
      logWeekError("week_page_init", cause, "WEEK_INIT");
    } finally {
      setLoading(false);
    }
  }, [ensureCorrelationId, fetchLatestReport, fetchWeekPayload, initData, isReady, logWeekError, mode]);

  useEffect(() => {
    void initPage();
  }, [initPage, pathname]);

  const week = useMemo(() => {
    return mapWeekReportToWeekBrief({
      weekBrief: payload?.week_brief_envelope?.data ?? payload?.week_brief ?? null,
      legacyWeekMap: payload?.week_map ?? DEFAULT_WEEK_MAP,
      chunks: payload?.chunks ?? null,
      latestReportId,
    });
  }, [payload, latestReportId]);

  useEffect(() => {
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
          week_type: week.weekType,
        },
        { correlationId: ensureCorrelationId(), flowId: FLOW_FORECAST_CATALOG, block: "WEEK_DAY_GRID" },
      );
    },
    [ensureCorrelationId, week.weekType],
  );

  const primaryHref = week.cta.primary?.href || (week.reportId ? `/read/${week.reportId}` : "/create?type=week_forecast");
  const primaryLabel = week.cta.primary?.label || (week.reportId ? "Открыть полный отчёт" : "Получить полный отчёт");

  if (!isReady || loading) {
    return (
      <ConsumerPageShell testId="week-page">
        <ConsumerPanel className="p-5">
          <LoadingState compact message="Собираем карту недели..." />
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  if (mode === "guest" || mode === "none" || !initData) {
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

  return (
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
          primaryHref={primaryHref}
          primaryLabel={primaryLabel}
          onPrimaryClick={() => {
            void trackCatalogEvent(
              week.reportId ? "week.open_full_report_click" : "week.premium_click",
              {
                surface: "week",
                flow_id: FLOW_FORECAST_CATALOG,
                correlation_id: ensureCorrelationId(),
                block: "WEEK_PRIMARY_CTA",
                week_type: week.weekType,
                cta_href: primaryHref,
              },
              { correlationId: ensureCorrelationId(), flowId: FLOW_FORECAST_CATALOG, block: "WEEK_PRIMARY_CTA" },
            );
          }}
        />

        <WeekDayGrid week={week} onDayClick={trackDayClick} />
        <WeekDomainPanel week={week} />
        <WeekActionsPanel week={week} />
        <WeekExplainabilityPanel week={week} />
        <WeekDeepSections week={week} />

        {week.fallbackMode ? (
          <ConsumerStatusBadge
            label="Fallback mode"
            description="Карта недели собрана в безопасном режиме"
            tone="amber"
            className="self-start"
          />
        ) : null}
      </section>
    </ConsumerPageShell>
  );
}

export default function WeekPage() {
  return (
    <Suspense fallback={<ConsumerPageShell testId="week-page"><ConsumerPanel className="p-5"><LoadingState compact message="Собираем карту недели..." /></ConsumerPanel></ConsumerPageShell>}>
      <WeekPageContent />
    </Suspense>
  );
}
