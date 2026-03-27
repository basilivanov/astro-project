"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowRight, Sparkles } from "lucide-react";
import { useTelegram } from "../../../hooks/useTelegram";
import { EmptyState, ErrorState, LoadingState } from "../../../components/ui-states";
import {
  ConsumerHero,
  ConsumerMetaPill,
  ConsumerPageShell,
  ConsumerPanel,
  ConsumerStatusBadge,
} from "../../../components/consumer-page-shell";
import { CatalogCheckoutResumeBanner } from "../../../components/catalog/catalog-checkout-resume";
import {
  setCatalogAnalyticsContext,
  startCatalogCorrelation,
  trackCatalogEvent,
} from "../../../components/catalog/catalog-analytics";
import { CATALOG_GRACE_BLOCKS, CATALOG_GRACE_MODULES, withCatalogTrace } from "../../../components/catalog/create-shared";

// START_MODULE_CONTRACT: M-REPORTS-HISTORY
// purpose: Render report history with strict-GRACE telemetry for filters, CTA flows, and checkout resume state.
// owns:
//   - frontend/app/reports/history/page.tsx
// inputs:
//   - Telegram auth/runtime state, query flags, report history API payload
// outputs:
//   - history UI, inline checkout resume banner, correlation-aware analytics
// dependencies:
//   - /api/reports/my
//   - catalog analytics helpers + CatalogCheckoutResumeBanner
// invariants:
//   - every telemetry event carries `FLOW-FORECAST-CATALOG` via trackCatalogEvent
//   - history surface uses stable semantic block labels
// non_goals:
//   - payment provider orchestration or read-page rendering
// END_MODULE_CONTRACT: M-REPORTS-HISTORY

// START_MODULE_MAP: M-REPORTS-HISTORY
// entrypoints:
//   - HistoryPage (default export)
// key_flows:
//   - analytics context bootstrap
//   - report history fetch
//   - filter / CTA tracking
//   - checkout resume banner for history surface
// owned_tests:
//   - frontend/e2e/history-cta.spec.ts
// adjacent_modules:
//   - frontend/components/catalog/catalog-checkout-resume.tsx
//   - frontend/components/catalog/catalog-analytics.ts
// END_MODULE_MAP: M-REPORTS-HISTORY

type UserReport = {
  id: string;
  report_type: string;
  status: string;
  created_at: string;
  client_name: string;
};

type HistoryFilterId = "all" | "natal" | "forecast" | "horary" | "synastry";

type HistoryFilterConfig = {
  id: HistoryFilterId;
  label: string;
  ctaLabel: string;
  ctaHref: string;
  emptyTitle: string;
  emptyMessage: string;
  match: (report: UserReport) => boolean;
};

const HISTORY_FILTERS: HistoryFilterConfig[] = [
  {
    id: "all",
    label: "Все разборы",
    ctaLabel: "Открыть каталог разборов",
    ctaHref: "/reports",
    emptyTitle: "История пока пустая",
    emptyMessage: "Первый заказ появится здесь. После этого будет удобно возвращаться к любому разбору без поиска по чату.",
    match: () => true,
  },
  {
    id: "natal",
    label: "Натал",
    ctaLabel: "Создать новый Натал",
    ctaHref: "/create?type=natal_master",
    emptyTitle: "Натала пока нет",
    emptyMessage: "Натальная карта станет точкой опоры для остальных персональных разборов и прогнозов.",
    match: (report) => report.report_type.includes("natal"),
  },
  {
    id: "forecast",
    label: "Прогнозы",
    ctaLabel: "Выбрать прогноз",
    ctaHref: "/reports",
    emptyTitle: "Прогнозов пока нет",
    emptyMessage: "Здесь будут сохраняться недельные, месячные, годовые и солярные сценарии.",
    match: (report) => report.report_type.includes("forecast") || report.report_type.includes("solar"),
  },
  {
    id: "horary",
    label: "Хорар",
    ctaLabel: "Создать новый Хорар",
    ctaHref: "/create?type=horary",
    emptyTitle: "Хораров пока нет",
    emptyMessage: "Разовый вопрос удобен, когда нужен быстрый ответ на конкретную ситуацию.",
    match: (report) => report.report_type.includes("horary"),
  },
  {
    id: "synastry",
    label: "Совместимость",
    ctaLabel: "Создать новый разбор совместимости",
    ctaHref: "/create?type=synastry",
    emptyTitle: "Разборов совместимости пока нет",
    emptyMessage: "Раздел пригодится, если хотите хранить историю разборов по отношениям отдельно от личных карт.",
    match: (report) => report.report_type.includes("synastry"),
  },
];

const formatHistoryReportType = (value: string) => {
  const map: Record<string, string> = {
    natal_master: "Натальная карта",
    year_forecast: "Альманах 2026",
    month_forecast: "Прогноз на месяц",
    week_forecast: "Прогноз на неделю",
    ten_year_forecast: "Прогноз на 10 лет",
    horary: "Вопрос",
    horary_answer: "Вопрос",
    synastry: "Совместимость",
    solar_return: "Соляр",
  };

  return map[value] || value.replace(/_/g, " ");
};

const formatDate = (dateString: string) =>
  new Date(dateString).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

const formatTime = (dateString: string) =>
  new Date(dateString).toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });

const getStatusLabel = (status: string) => {
  switch (status) {
    case "completed":
      return { text: "Готов", className: "border-emerald-100 bg-emerald-50 text-emerald-700" };
    case "in_progress":
      return { text: "В работе", className: "border-amber-100 bg-amber-50 text-amber-700" };
    case "failed":
      return { text: "Ошибка", className: "border-rose-100 bg-rose-50 text-rose-700" };
    default:
      return { text: "Ожидание", className: "border-slate-200 bg-slate-50 text-slate-600" };
  }
};

const getReportFamily = (reportType: string) => {
  if (reportType.includes("natal")) return "Личный разбор";
  if (reportType.includes("forecast") || reportType.includes("solar")) return "Прогноз";
  if (reportType.includes("horary")) return "Точечный вопрос";
  if (reportType.includes("synastry")) return "Отношения";
  return "Разбор";
};

const formatReportCount = (count: number) => {
  const mod10 = count % 10;
  const mod100 = count % 100;

  if (mod10 === 1 && mod100 !== 11) {
    return `${count} разбор`;
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return `${count} разбора`;
  }
  return `${count} разборов`;
};

export default function HistoryPage() {
  const searchParams = useSearchParams();
  const checkoutToken = searchParams.get("checkout");
  const mockEnabled = searchParams.get("mock") === "1";
  const runtimeEnabled = searchParams.get("runtime") === "1";
  const { initData, isReady, mode, user } = useTelegram();
  const [reports, setReports] = useState<UserReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<HistoryFilterId>("all");
  const [requestKey, setRequestKey] = useState(0);

  const activeFilter = useMemo(
    () => HISTORY_FILTERS.find((item) => item.id === filter) || HISTORY_FILTERS[0],
    [filter],
  );

  const filteredReports = useMemo(
    () => reports.filter((report) => activeFilter.match(report)),
    [activeFilter, reports],
  );

  const completedReportsCount = reports.filter((report) => report.status === "completed").length;
  const historyShellAnalytics = useMemo(
    () => ({
      event_name: "catalog.history_view",
      payload: withCatalogTrace(
        { surface: "history", entry_point: "history-page-shell" },
        {
          module: CATALOG_GRACE_MODULES.reportsHistory,
          contract: "FN-HISTORY-VIEW",
          block: "SHELL_RENDER",
          semantic_block: "SHELL_RENDER",
        },
      ),
    }),
    [],
  );

  // START_CONTRACT: FN-BOOTSTRAP-HISTORY-CONTEXT
  // purpose: Initialize history analytics context with correlation + checkout token.
  // inputs: telegram user id, checkout token.
  // side_effects: updates catalog analytics shared context.
  // END_CONTRACT: FN-BOOTSTRAP-HISTORY-CONTEXT
  useEffect(() => {
    // START_BLOCK: ANALYTICS_CONTEXT_BOOTSTRAP
    const correlationId = startCatalogCorrelation(checkoutToken ? "history_checkout_resume" : "history_view");
    setCatalogAnalyticsContext({
      user_id: user?.id,
      checkout_token: checkoutToken ?? undefined,
      correlation_id: correlationId,
    });
    // END_BLOCK: ANALYTICS_CONTEXT_BOOTSTRAP
  }, [checkoutToken, user?.id]);

  // START_CONTRACT: FN-LOAD-HISTORY-STATE
  // purpose: Fetch user reports and emit block-aware lifecycle telemetry.
  // inputs: telegram auth state, mock/runtime flags, retry key.
  // side_effects:
  //   - requests `/api/reports/my`
  //   - updates local reports/loading/error state
  //   - emits history lifecycle events
  // END_CONTRACT: FN-LOAD-HISTORY-STATE
  useEffect(() => {
    if (!isReady) {
      return;
    }

    if (mode === "guest" || mode === "none" || !initData) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    const loadReports = async () => {
      setLoading(true);
      setError(null);

      try {
        // START_BLOCK: DATA_FETCH
        void trackCatalogEvent("catalog.history_start", withCatalogTrace({
          surface: "history",
          entry_point: "history-page-load",
        }, {
          module: CATALOG_GRACE_MODULES.reportsHistory,
          contract: "FN-LOAD-HISTORY-STATE",
          block: CATALOG_GRACE_BLOCKS.history.dataFetch,
        }));
        const url = new URL("/api/reports/my", window.location.origin);
        if (mode === "mock" || window.location.search.includes("mock=1")) {
          url.searchParams.set("mock", "1");
        }
        if (runtimeEnabled) {
          url.searchParams.set("runtime", "1");
        }

        const response = await fetch(url.toString(), {
          headers: {
            "X-Telegram-Auth": initData,
          },
        });

        if (!response.ok) {
          throw new Error("Не удалось загрузить историю разборов");
        }

        const payload = await response.json();
        if (!cancelled) {
          setReports(Array.isArray(payload) ? payload : []);
          void trackCatalogEvent("catalog.history_success", withCatalogTrace({
            surface: "history",
            entry_point: "history-page-load",
          }, {
            module: CATALOG_GRACE_MODULES.reportsHistory,
            contract: "FN-LOAD-HISTORY-STATE",
            block: CATALOG_GRACE_BLOCKS.history.dataFetch,
          }));
        }
      } catch (loadError) {
        if (!cancelled) {
          setReports([]);
          setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить историю разборов");
          void trackCatalogEvent("catalog.history_error", withCatalogTrace({
            surface: "history",
            entry_point: "history-page-load",
          }, {
            module: CATALOG_GRACE_MODULES.reportsHistory,
            contract: "FN-LOAD-HISTORY-STATE",
            block: CATALOG_GRACE_BLOCKS.history.dataFetch,
          }));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
      // END_BLOCK: DATA_FETCH
    };

    loadReports();

    return () => {
      cancelled = true;
    };
  }, [initData, isReady, mode, requestKey, runtimeEnabled]);

  // START_CONTRACT: FN-HANDLE-FILTER-CHANGE
  // purpose: Update active filter and track user intent.
  // inputs: next history filter id.
  // side_effects: updates local filter state and telemetry.
  // END_CONTRACT: FN-HANDLE-FILTER-CHANGE
  const handleFilterChange = useCallback(
    (next: HistoryFilterId) => {
      setFilter(next);
      void trackCatalogEvent("catalog.history_filter", withCatalogTrace({
        surface: "history",
        entry_point: "history-filter-chip",
        filter_id: next,
      }, {
        module: CATALOG_GRACE_MODULES.reportsHistory,
        contract: "FN-HANDLE-FILTER-CHANGE",
        block: CATALOG_GRACE_BLOCKS.history.ctaTracking,
      }));
    },
    [],
  );

  // START_CONTRACT: FN-TRACK-HISTORY-CTA
  // purpose: Emit canonical CTA event for history surface.
  // inputs: action id and destination href.
  // END_CONTRACT: FN-TRACK-HISTORY-CTA
  const trackHistoryCta = useCallback(
    (action: string, href: string) => {
      void trackCatalogEvent("catalog.history_cta", withCatalogTrace({
        surface: "history",
        action,
        filter_id: activeFilter.id,
        cta_href: href,
        entry_point: action,
      }, {
        module: CATALOG_GRACE_MODULES.reportsHistory,
        contract: "FN-TRACK-HISTORY-CTA",
        block: CATALOG_GRACE_BLOCKS.history.ctaTracking,
      }));
    },
    [activeFilter.id],
  );

  // START_CONTRACT: FN-TRACK-HISTORY-REPORT-OPEN
  // purpose: Track transition from history card to read page.
  // inputs: report id + report_type.
  // END_CONTRACT: FN-TRACK-HISTORY-REPORT-OPEN
  const trackReportOpen = useCallback((report: UserReport) => {
    void trackCatalogEvent("catalog.history_open_report", withCatalogTrace({
      surface: "history",
      entry_point: "history-report-card",
      report_type: report.report_type,
      report_id: report.id,
    }, {
      module: CATALOG_GRACE_MODULES.reportsHistory,
      contract: "FN-TRACK-HISTORY-REPORT-OPEN",
      block: CATALOG_GRACE_BLOCKS.history.ctaTracking,
    }));
  }, []);

  if (!isReady || loading) {
    return (
      <ConsumerPageShell
        testId="reports-history-page"
        analyticsEvent={historyShellAnalytics}
      >
        <ConsumerHero
          eyebrow="История"
          title="История разборов"
          description="Собираем ваши прошлые заказы и прогружаем быстрые переходы к чтению."
          status={
            <ConsumerStatusBadge
              label="Загрузка"
              description="Подтягиваем каталог прошлых разборов"
              tone="slate"
            />
          }
        />
        <ConsumerPanel className="p-5">
          <LoadingState compact message="Собираем историю разборов..." />
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  if (mode === "guest" || mode === "none" || !initData) {
    return (
      <ConsumerPageShell
        testId="reports-history-page"
        analyticsEvent={historyShellAnalytics}
      >
        <ConsumerHero
          eyebrow="История"
          title="История разборов"
          description="Чтобы показать ваши сохраненные материалы, нужно открыть экран из Telegram и подтвердить доступ к профилю."
          status={
            <ConsumerStatusBadge
              label="Нужен вход"
              description="История связана с Telegram-профилем"
              tone="slate"
            />
          }
          actions={
            <Link
              href="/reports"
              onClick={() => trackHistoryCta("catalog_link", "/reports")}
              className="inline-flex items-center justify-center rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
            >
              К каталогу разборов
            </Link>
          }
        />
        <ConsumerPanel className="p-5">
          <EmptyState
            compact
            title="История пока недоступна"
            message="Откройте экран из бота, чтобы мы проверили привязку к вашему профилю и показали сохраненные разборы."
            actionLabel="К каталогу разборов"
            actionHref="/reports"
            onActionClick={() => trackHistoryCta("catalog_link", "/reports")}
          />
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  if (error) {
    return (
      <ConsumerPageShell
        testId="reports-history-page"
        analyticsEvent={{ event_name: "catalog.history_view", payload: withCatalogTrace({ surface: "history" }, { module: CATALOG_GRACE_MODULES.reportsHistory, contract: "FN-HISTORY-VIEW", block: "SHELL_RENDER" }) }}
      >
        <ConsumerHero
          eyebrow="История"
          title="История разборов"
          description="Экран сохранил структуру, но данные не загрузились с первого раза. Повторная попытка должна восстановить список без потери сценария."
          status={
            <ConsumerStatusBadge
              label="Нужен повтор"
              description="Сервис истории временно не ответил"
              tone="rose"
            />
          }
          actions={
            <Link
              href="/reports"
              onClick={() => trackHistoryCta("catalog_link", "/reports")}
              className="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-indigo-200 hover:text-indigo-700"
            >
              К каталогу разборов
            </Link>
          }
        />
        <ConsumerPanel className="border-rose-100 p-5">
          <ErrorState compact error={error} onRetry={() => setRequestKey((value) => value + 1)} />
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  return (
    <ConsumerPageShell
      testId="reports-history-page"
      analyticsEvent={historyShellAnalytics}
    >
      <ConsumerHero
        eyebrow="История"
        title="История разборов"
        description="Личные карты, прогнозы и хорары собраны в одном месте. Отсюда удобно вернуться к чтению, проверить статус и быстро перейти к новому заказу."
        status={
          <ConsumerStatusBadge
            label={formatReportCount(filteredReports.length)}
            description={filteredReports.length > 0 ? "В текущем фильтре" : "Фильтр пока пуст"}
            tone={filteredReports.length > 0 ? "indigo" : "slate"}
          />
        }
        meta={
          <>
            <ConsumerMetaPill label="Всего" value={formatReportCount(reports.length)} />
            <ConsumerMetaPill label="Готово" value={formatReportCount(completedReportsCount)} />
            <ConsumerMetaPill label="Фильтр" value={activeFilter.label} />
          </>
        }
          actions={
            <>
              <Link
                href="/reports"
                onClick={() => trackHistoryCta("catalog_link", "/reports")}
                className="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-indigo-200 hover:text-indigo-700"
              >
                Каталог разборов
              </Link>
              <Link
                href={activeFilter.ctaHref}
                data-testid="history-filter-cta"
                data-block={CATALOG_GRACE_BLOCKS.history.ctaTracking}
                onClick={() => trackHistoryCta("filter_cta", activeFilter.ctaHref)}
                className="inline-flex items-center justify-center rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
              >
                {activeFilter.ctaLabel}
              </Link>
            </>
          }
      />

      <CatalogCheckoutResumeBanner
        surface="history"
        entryPoint="history-inline-resume"
        checkoutToken={checkoutToken}
        mockEnabled={mockEnabled}
        runtimeEnabled={runtimeEnabled}
        initData={initData}
        isReady={isReady}
        mode={mode}
      />

      <ConsumerPanel className="p-4 sm:p-5">
        {/* START_BLOCK: RESUME_STATE */}
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-2">
            {HISTORY_FILTERS.map((item) => {
              const isActive = item.id === activeFilter.id;

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleFilterChange(item.id)}
                  className={`rounded-full px-4 py-2.5 text-sm font-semibold transition ${
                    isActive
                      ? "bg-slate-950 text-white shadow-sm"
                      : "border border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-900"
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </div>

          <div className="rounded-[24px] border border-slate-100 bg-slate-50/80 p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white text-indigo-600 shadow-sm">
                <Sparkles size={18} />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">
                  Текущий фокус
                </p>
                <p className="mt-2 text-sm font-semibold leading-relaxed text-slate-800">
                  {activeFilter.id === "all"
                    ? "Смотрите всю библиотеку разборов или уходите в каталог за новым сценарием."
                    : `Фильтр "${activeFilter.label}" собрал только релевантные материалы и предлагает быстрый следующий шаг.`}
                </p>
              </div>
            </div>
          </div>
        </div>
        {/* END_BLOCK: RESUME_STATE */}
      </ConsumerPanel>

      {filteredReports.length === 0 ? (
        <ConsumerPanel className="p-5">
          <EmptyState
            compact
            title={activeFilter.emptyTitle}
            message={activeFilter.emptyMessage}
            actionLabel={activeFilter.ctaLabel}
            actionHref={activeFilter.ctaHref}
            onActionClick={() => trackHistoryCta("empty_state_cta", activeFilter.ctaHref)}
          />
        </ConsumerPanel>
      ) : (
        <section className="grid gap-4" aria-label="Список разборов">
          {filteredReports.map((report) => {
            const status = getStatusLabel(report.status);
            const clientName = report.client_name?.trim() || "Личный профиль";

            return (
              <Link
                key={report.id}
                href={`/read/${report.id}`}
                onClick={() => trackReportOpen(report)}
                className="group block"
                aria-label={`${formatHistoryReportType(report.report_type)}: ${clientName}`}
              >
                <ConsumerPanel className="border-white/80 p-5 transition duration-200 group-hover:-translate-y-0.5 group-hover:border-indigo-100 group-hover:shadow-[0_28px_70px_-38px_rgba(79,70,229,0.35)]">
                  <div className="flex flex-col gap-5">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0">
                        <p className="text-[11px] font-black uppercase tracking-[0.24em] text-slate-400">
                          {getReportFamily(report.report_type)}
                        </p>
                        <h2 className="mt-2 text-2xl font-black tracking-tight text-slate-950">
                          {formatHistoryReportType(report.report_type)}
                        </h2>
                        <p className="mt-2 text-sm leading-relaxed text-slate-600">
                          {clientName}
                        </p>
                      </div>
                      <span
                        className={`inline-flex items-center self-start rounded-full border px-3 py-1 text-[11px] font-black uppercase tracking-[0.16em] ${status.className}`}
                      >
                        {status.text}
                      </span>
                    </div>

                    <div className="grid gap-2 sm:grid-cols-3">
                      <ConsumerMetaPill label="Дата" value={formatDate(report.created_at)} />
                      <ConsumerMetaPill label="Время" value={formatTime(report.created_at)} />
                      <ConsumerMetaPill label="Профиль" value={clientName} />
                    </div>

                    <div className="flex items-center justify-between border-t border-slate-100 pt-4">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-slate-700">Открыть разбор</p>
                        <p className="mt-1 text-xs font-medium text-slate-500">
                          Вернуться к чтению без поиска по чату и истории платежей.
                        </p>
                      </div>
                      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-400 transition group-hover:border-indigo-200 group-hover:text-indigo-600">
                        <ArrowRight size={18} />
                      </span>
                    </div>
                  </div>
                </ConsumerPanel>
              </Link>
            );
          })}
        </section>
      )}
    </ConsumerPageShell>
  );
}
