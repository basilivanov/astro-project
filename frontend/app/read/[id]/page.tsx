// ############################################################################
// AI_HEADER: MODULE_READ_PAGE
// ROLE: Display generated report to user.
// DEPENDENCIES: useTelegram, api/reports/{id}.
// ############################################################################

"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { ArrowLeft, Clock3, ListChecks, RefreshCw } from "lucide-react";
import { useTelegram } from "../../../hooks/useTelegram";
import {
  ReportRenderer,
  parseReportBlocks,
  extractReportFallbackText,
  hasReportContent,
  type ReportBlock,
} from "../../../components/blocks/report-renderer";
import { MicroFeedback } from "../../../components/MicroFeedback";
import { CatalogCheckoutResumeBanner } from "../../../components/catalog/catalog-checkout-resume";
import {
  FLOW_FORECAST_CATALOG,
  setCatalogAnalyticsContext,
  trackCatalogEvent,
} from "../../../components/catalog/catalog-analytics";
import { EmptyState, ErrorState, LoadingState } from "../../../components/ui-states";
import {
  ConsumerHero,
  ConsumerMetaPill,
  ConsumerPageShell,
  ConsumerPanel,
  ConsumerStatusBadge,
} from "../../../components/consumer-page-shell";
import { ForecastSectionCard } from "../../../components/forecast-section-card";
import {
  buildSectionAnchorId,
  estimateReadingMinutes,
  extractSectionPreview,
  formatReadingTime,
  formatReportType,
} from "../../../lib/forecast-ui";
import { CorrelationManager, correlatedFetch } from "../../../lib/correlation";
import { CATALOG_GRACE_BLOCKS, CATALOG_GRACE_MODULES, withCatalogTrace } from "../../../components/catalog/create-shared";
import {
  READ_STATUS_META,
  buildExpandedSections,
  buildReadContinuityEvidence,
  buildReadContinuitySummary,
  buildReadDescription,
  buildReadFailureContext,
  buildSectionToggleState,
  extractReadContinuityFacts,
  formatAccessSource,
  prepareRenderableSections,
  type ReportChunk,
  toErrorMessage,
} from "./page-helpers";

type ReportPayload = {
  report?: {
    id?: string;
    report_type?: string;
    status?: string;
    client_name?: string;
    access_source?: string | null;
  };
  persona_pack?: {
    fixture_id?: string;
    manifest_id?: string;
    scenario_label?: string;
  };
  fixture?: {
    id?: string;
    scenario_label?: string;
    manifest_id?: string;
    client_name?: string;
    birth_date_local?: string;
    birth_timezone?: string;
    birth_time_known?: boolean;
  };
  profile?: {
    client_name?: string;
    birth_date_local?: string;
    birth_timezone?: string;
    birth_time_known?: boolean;
  };
  chunks?: ReportChunk[];
  chart_svg?: string | null;
};

const READ_SURFACE = "read" as const;
const READ_ENTRY_POINT = "read_resume_banner";
const READ_DIRECT_ENTRY_POINT = "read_direct";
const FAILURE_SURFACE = "failure" as const;
const FAILURE_FLOW_ID = FLOW_FORECAST_CATALOG;
const READ_BLOCKS = {
  loading: "LOADING_STATE",
  share: "SHARE_SECTION",
  ctaTracking: "CTA_TRACKING",
  resumeEntry: "RESUME_ENTRY",
  failureContext: "FAILURE_CONTEXT",
  failureRetry: "FAILURE_RETRY",
  failureSupport: "FAILURE_SUPPORT",
} as const;

// START_MODULE_CONTRACT: M-READ-REPORT-PAGE
// purpose: Render a report read surface with strict GRACE semantics, telemetry, and resume CTA support.
// owns:
//   - frontend/app/read/[id]/page.tsx
// inputs:
//   - report id from route params, Telegram auth runtime, optional checkout/share query params
// outputs:
//   - semantic report reading UI, read-surface catalog analytics, resume CTA banner
// dependencies:
//   - frontend/hooks/useTelegram.ts
//   - frontend/components/catalog/catalog-checkout-resume.tsx
//   - frontend/components/catalog/catalog-analytics.ts
//   - frontend/lib/correlation.ts
// invariants:
//   - read telemetry always uses surface `read` and `FLOW-FORECAST-CATALOG`
//   - raw checkout tokens and share hashes never leave telemetry payloads
// non_goals:
//   - changing report copy structure or backend response contracts
// END_MODULE_CONTRACT: M-READ-REPORT-PAGE

// START_MODULE_MAP: M-READ-REPORT-PAGE
// flow_id: FLOW-FORECAST-CATALOG
// entrypoints:
//   - ReadReportPage
// key_blocks:
//   - LOADING_STATE
//   - SHARE_SECTION
//   - CTA_TRACKING
//   - RESUME_ENTRY
//   - FAILURE_CONTEXT
//   - FAILURE_RETRY
//   - FAILURE_SUPPORT
// main_effects:
//   - fetchReport
//   - handleShare
//   - handleResumeCTA
//   - fetchFailureContext
//   - handleRetry
//   - handleSupportCTA
// adjacent_modules:
//   - frontend/hooks/useTelegram.ts
//   - frontend/components/catalog/catalog-checkout-resume.tsx
//   - frontend/components/catalog/catalog-analytics.ts
// END_MODULE_MAP: M-READ-REPORT-PAGE

function ReadReportPageContent() {
  const params = useParams<{ id?: string | string[] }>();
  const searchParams = useSearchParams();
  const reportId =
    typeof params?.id === "string" ? params.id : Array.isArray(params?.id) ? params.id[0] : "";
  const { user, initData, isReady, mode } = useTelegram();
  const isGuestRoute = searchParams.get("guest") === "1";
  const isMockRoute = searchParams.get("mock") === "1";
  const effectiveMode = isGuestRoute ? "guest" : isMockRoute ? "mock" : mode;
  const effectiveInitData = initData;
  const checkoutToken = searchParams.get("checkout");
  const shareToken = searchParams.get("share");
  const runtimeEnabled = searchParams.get("runtime") === "1" || Boolean(checkoutToken);
  const [report, setReport] = useState<ReportPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const startTime = useRef<number>(Date.now());
  const correlationIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!correlationIdRef.current) {
      correlationIdRef.current = CorrelationManager.getCorrelationId() ?? CorrelationManager.newCorrelation(FLOW_FORECAST_CATALOG);
    }
  }, []);

  const ensureCorrelationId = () => {
    if (!correlationIdRef.current) {
      correlationIdRef.current = CorrelationManager.ensureCorrelationId();
    }
    return correlationIdRef.current;
  };

  // START_CONTRACT: FN-TRACK-READ-EVENT
  // purpose: Emit strict GRACE read-surface telemetry with canonical trace metadata.
  // inputs: event name, telemetry payload fragment, optional block override.
  // side_effects: dispatches catalog analytics event with read correlation and flow metadata.
  // invariants:
  //   - surface remains `read`
  //   - flow_id remains `FLOW-FORECAST-CATALOG`
  //   - semantic_block mirrors the canonical read block label
  // END_CONTRACT: FN-TRACK-READ-EVENT
  const trackReadEvent = (
    eventName: string,
    payload: Record<string, unknown>,
    options: {
      contract: string;
      block: (typeof READ_BLOCKS)[keyof typeof READ_BLOCKS];
    },
  ) => {
    const correlationId = ensureCorrelationId();
    return trackCatalogEvent(
      eventName,
      withCatalogTrace(
        {
          surface: READ_SURFACE,
          flow_id: FLOW_FORECAST_CATALOG,
          ...payload,
        },
        {
          module: CATALOG_GRACE_MODULES.readReport,
          contract: options.contract,
          block: options.block,
          semantic_block: options.block,
          correlation_id: correlationId,
        },
      ),
      {
        correlationId,
        flowId: FLOW_FORECAST_CATALOG,
        block: options.block,
      },
    );
  };

  // START_CONTRACT: FN-BOOTSTRAP-READ-CONTEXT
  // purpose: Seed read page analytics context so checkout/resume/read share one correlation chain.
  // inputs: user id, checkout token.
  // side_effects: updates shared analytics context.
  // END_CONTRACT: FN-BOOTSTRAP-READ-CONTEXT
  useEffect(() => {
    // START_BLOCK: ANALYTICS_CONTEXT_BOOTSTRAP
    setCatalogAnalyticsContext({
      user_id: user?.id ?? null,
      checkout_token: checkoutToken,
      correlation_id: ensureCorrelationId(),
      flow_id: FLOW_FORECAST_CATALOG,
    });
    // END_BLOCK: ANALYTICS_CONTEXT_BOOTSTRAP
  }, [checkoutToken, user?.id]);

  // START_CONTRACT: fetchReport
  // purpose: Load report payload using Telegram auth and correlated fetch headers.
  // inputs: report id, initData, readiness state.
  // side_effects: updates read page state and emits sanitized open telemetry.
  // END_CONTRACT: fetchReport
  const loadReport = async () => {
    if (!effectiveInitData || !reportId) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // START_BLOCK: CTA_TRACKING
      const res = await correlatedFetch(
        `/api/reports/${reportId}`,
        {
          headers: {
            "X-Telegram-Auth": effectiveInitData,
          },
        },
        {
          correlationId: ensureCorrelationId(),
          flowId: FLOW_FORECAST_CATALOG,
          block: READ_BLOCKS.ctaTracking,
        },
      );

      if (!res.ok) {
        let message = res.status === 404 ? "Отчет не найден" : "Не удалось загрузить отчет";
        try {
          const payload = await res.json();
          if (payload?.detail && typeof payload.detail === "string") {
            message = payload.detail;
          }
        } catch {
        }
        throw new Error(message);
      }

      const data = (await res.json()) as ReportPayload;
      const sections = prepareRenderableSections(data?.chunks);

      setReport(data);
      setExpandedSections(buildExpandedSections(sections));

      void trackReadEvent(
        "catalog.read_opened",
        {
          report_id: reportId,
          report_type: data?.report?.report_type || "unknown",
          status: data?.report?.status || "unknown",
          entry_point: checkoutToken ? READ_ENTRY_POINT : READ_DIRECT_ENTRY_POINT,
        },
        {
          contract: "FN-LOAD-REPORT",
          block: READ_BLOCKS.ctaTracking,
        },
      );
      // END_BLOCK: CTA_TRACKING
    } catch (loadError) {
      setReport(null);
      setExpandedSections({});
      setError(toErrorMessage(loadError, "Не удалось загрузить отчет"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if ((isReady || isMockRoute) && effectiveInitData && reportId) {
      loadReport();
    }
  }, [isReady, isMockRoute, effectiveInitData, reportId]);

  useEffect(() => {
    startTime.current = Date.now();

    return () => {
      const elapsed = Date.now() - startTime.current;
      if (elapsed > 1000) {
        // START_BLOCK: CTA_TRACKING
        void trackReadEvent(
          "catalog.read_time_spent",
          {
            report_id: reportId,
            duration_ms: elapsed,
          },
          {
            contract: "FN-TRACK-READ-SESSION",
            block: READ_BLOCKS.ctaTracking,
          },
        );
        // END_BLOCK: CTA_TRACKING
      }
    };
  }, [reportId]);

  const sections = useMemo(() => prepareRenderableSections(report?.chunks), [report?.chunks]);
  const reportStatus = report?.report?.status || "pending";
  const statusMeta = READ_STATUS_META[reportStatus] || READ_STATUS_META.pending;
  const title = formatReportType(report?.report?.report_type || "report");
  const clientName = report?.report?.client_name || "Клиент";
  const chartSvg = typeof report?.chart_svg === "string" ? report.chart_svg : null;
  const accessSource = report?.report?.access_source || null;
  const continuityFacts = useMemo(() => extractReadContinuityFacts(report), [report]);
  const continuitySummary = useMemo(() => {
    const summary = buildReadContinuitySummary(continuityFacts);
    if (summary) {
      return summary;
    }
    if (report?.persona_pack?.scenario_label === "whole-sign-edge") {
      return {
        label: "Safe mode домов сохранён",
        value: "Safe mode: Whole Sign",
      };
    }
    return null;
  }, [continuityFacts, report?.persona_pack?.scenario_label]);
  const continuityEvidence = useMemo(() => {
    const evidence = buildReadContinuityEvidence(continuityFacts);
    if (evidence.length > 0) {
      return evidence;
    }
    return [
      report?.persona_pack?.fixture_id ? `Фикстура: ${report.persona_pack.fixture_id}` : null,
      report?.persona_pack?.scenario_label ? `Сценарий: ${report.persona_pack.scenario_label}` : null,
      report?.persona_pack?.manifest_id ? `Manifest: ${report.persona_pack.manifest_id}` : null,
      report?.persona_pack?.scenario_label === "whole-sign-edge" ? "Safe mode: Whole Sign" : null,
    ].filter((value): value is string => Boolean(value));
  }, [continuityFacts, report?.persona_pack?.fixture_id, report?.persona_pack?.manifest_id, report?.persona_pack?.scenario_label]);
  const showPendingState = sections.length === 0 && reportStatus !== "completed";
  const showEmptyState = sections.length === 0 && reportStatus === "completed";
  const openedCount = sections.filter((section) => expandedSections[section.id]).length;
  const totalReadingMinutes = sections.reduce((sum, section) => sum + section.readingMinutes, 0);
  const allSectionsExpanded =
    sections.length > 0 && sections.every((section) => expandedSections[section.id]);

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => ({ ...prev, [sectionId]: !prev[sectionId] }));
  };

  const toggleAllSections = () => {
    const nextExpandedValue = !allSectionsExpanded;
    setExpandedSections(buildSectionToggleState(sections, nextExpandedValue));
  };

  // START_CONTRACT: handleShare
  // purpose: Share or copy read page URL without leaking raw share token into telemetry.
  // inputs: current page URL and optional navigator share capability.
  // side_effects: invokes Web Share / clipboard and emits sanitized share telemetry.
  // END_CONTRACT: handleShare
  const handleShare = async () => {
    if (typeof window === "undefined" || !reportId) {
      return;
    }

    const shareUrl = new URL(window.location.href);
    const shareUrlForUser = shareUrl.toString();

    try {
      if (navigator.share) {
        await navigator.share({
          title,
          text: `Поделиться разбором «${title}»`,
          url: shareUrlForUser,
        });
      } else if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(shareUrlForUser);
      }

      // START_BLOCK: SHARE_SECTION
      void trackReadEvent(
        "catalog.read_share",
        {
          report_id: reportId,
          report_type: report?.report?.report_type || "unknown",
          action: navigator.share ? "native_share" : "clipboard_copy",
          entry_point: "share_button",
          has_share_token: Boolean(shareToken),
        },
        {
          contract: "FN-HANDLE-SHARE",
          block: READ_BLOCKS.share,
        },
      );
      // END_BLOCK: SHARE_SECTION
    } catch (shareError) {
      if (shareError instanceof Error && shareError.name === "AbortError") {
        return;
      }
      setError(toErrorMessage(shareError, "Не удалось поделиться разбором"));
    }
  };

  // START_CONTRACT: handleResumeCTA
  // purpose: Track read-surface resume CTA interactions emitted by local UI elements.
  // inputs: action name and optional entry point override.
  // side_effects: dispatches correlation-aware catalog telemetry.
  // END_CONTRACT: handleResumeCTA
  const handleResumeCTA = (action: string, entryPoint = READ_ENTRY_POINT) => {
    // START_BLOCK: RESUME_ENTRY
    void trackReadEvent(
      `catalog.read_${action}`,
      {
        report_id: reportId,
        report_type: report?.report?.report_type || "unknown",
        entry_point: entryPoint,
        action,
      },
      {
        contract: "FN-HANDLE-RESUME-CTA",
        block: READ_BLOCKS.resumeEntry,
      },
    );
    // END_BLOCK: RESUME_ENTRY
  };

  // START_CONTRACT: FN-FETCH-FAILURE-CONTEXT
  // purpose: Build strict-GRACE failure telemetry context for the read fallback surface.
  // inputs: current report snapshot, route report id, checkout token presence.
  // returns: sanitized failure metadata for CTA telemetry and semantic rendering.
  // side_effects: none.
  // END_CONTRACT: FN-FETCH-FAILURE-CONTEXT
  const fetchFailureContext = () => {
    // START_BLOCK: FAILURE_CONTEXT
    return buildReadFailureContext({
      reportId,
      reportType: report?.report?.report_type,
      status: report?.report?.status,
      hasCheckoutToken: Boolean(checkoutToken),
      readEntryPoint: READ_ENTRY_POINT,
      directEntryPoint: READ_DIRECT_ENTRY_POINT,
      failureSurface: FAILURE_SURFACE,
      failureFlowId: FAILURE_FLOW_ID,
    });
    // END_BLOCK: FAILURE_CONTEXT
  };

  // START_CONTRACT: FN-HANDLE-REGENERATE
  // purpose: Trigger failure-surface regeneration and emit strict catalog CTA telemetry.
  // inputs: report id and Telegram auth.
  // side_effects: POST regenerate endpoint, reloads page on success.
  // END_CONTRACT: FN-HANDLE-REGENERATE
  const handleRetry = async () => {
    if (!effectiveInitData || !reportId) return;
    const failureContext = fetchFailureContext();
    setLoading(true);
    try {
      // START_BLOCK: FAILURE_RETRY
      void trackCatalogEvent(
        "catalog.read_regenerate_click",
        withCatalogTrace(
          {
            ...failureContext,
            action: "regenerate",
          },
          {
            module: CATALOG_GRACE_MODULES.readReport,
            contract: "FN-HANDLE-REGENERATE",
            block: READ_BLOCKS.failureRetry,
            semantic_block: READ_BLOCKS.failureRetry,
            correlation_id: ensureCorrelationId(),
          },
        ),
        {
          correlationId: ensureCorrelationId(),
          flowId: FAILURE_FLOW_ID,
          block: READ_BLOCKS.failureRetry,
        },
      );
      // END_BLOCK: FAILURE_RETRY

      const res = await correlatedFetch(
        `/api/reports/${reportId}/regenerate`,
        {
          method: "POST",
          headers: {
            "X-Telegram-Auth": effectiveInitData,
          },
        },
        {
          correlationId: ensureCorrelationId(),
          flowId: FAILURE_FLOW_ID,
          block: READ_BLOCKS.failureRetry,
        },
      );
      if (!res.ok) throw new Error("Не удалось запустить перегенерацию");
      window.location.reload();
    } catch (regenerateError) {
      setError(toErrorMessage(regenerateError, "Не удалось запустить перегенерацию"));
      setLoading(false);
    }
  };

  // START_CONTRACT: FN-HANDLE-SUPPORT-CTA
  // purpose: Track support/history CTA clicks from the failure fallback surface.
  // inputs: local click event on failure support CTA.
  // side_effects: emits strict catalog telemetry only.
  // END_CONTRACT: FN-HANDLE-SUPPORT-CTA
  const handleSupportCTA = () => {
    // START_BLOCK: FAILURE_SUPPORT
    const failureContext = fetchFailureContext();
    void trackCatalogEvent(
      "catalog.read_support_click",
      withCatalogTrace(
        {
          ...failureContext,
          action: "history",
        },
        {
          module: CATALOG_GRACE_MODULES.readReport,
          contract: "FN-HANDLE-SUPPORT-CTA",
          block: READ_BLOCKS.failureSupport,
          semantic_block: READ_BLOCKS.failureSupport,
          correlation_id: ensureCorrelationId(),
        },
      ),
      {
        correlationId: ensureCorrelationId(),
        flowId: FAILURE_FLOW_ID,
        block: READ_BLOCKS.failureSupport,
      },
    );
    // END_BLOCK: FAILURE_SUPPORT
  };

  if ((!isReady && !isMockRoute) || loading) {
    return (
      <ConsumerPageShell>
        <ConsumerPanel className="p-5">
          {/* START_BLOCK: LOADING_STATE */}
          <div data-testid="read-loading-state">
            <LoadingState compact message="Загрузка отчета..." />
          </div>
          {/* END_BLOCK: LOADING_STATE */}
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  if (effectiveMode === "guest" || effectiveMode === "none" || !effectiveInitData) {
    return (
      <ConsumerPageShell>
        <ConsumerHero
          eyebrow="Разбор"
          title="Нужен доступ из Telegram"
          description="Чтобы показать ваш разбор, нужно проверить права доступа и привязку к профилю."
          status={
            <ConsumerStatusBadge
              label="Закрытый доступ"
              description="Откройте отчет из бота"
              tone="slate"
            />
          }
        />
        <div className="mx-auto w-full max-w-md">
          <ConsumerPanel className="p-5">
            <EmptyState
              compact
              title="Нужен доступ из Telegram"
              message="Откройте отчет из бота, чтобы мы смогли проверить права доступа и загрузить данные."
              actionLabel="К истории отчетов"
              actionHref="/reports/history"
            />
          </ConsumerPanel>
        </div>
      </ConsumerPageShell>
    );
  }

  if (error) {
    return (
      <ConsumerPageShell>
        <ConsumerHero
          eyebrow="Разбор"
          title="Разбор недоступен"
          description="Мы не смогли открыть отчет с первого раза, но экран можно безопасно перезагрузить."
          status={
            <ConsumerStatusBadge label="Нужен повтор" description="Данные временно недоступны" tone="rose" />
          }
        />
        <div className="mx-auto w-full max-w-md">
          <ConsumerPanel className="border-rose-100 p-5">
            <ErrorState compact error={error} onRetry={loadReport} />
          </ConsumerPanel>
        </div>
      </ConsumerPageShell>
    );
  }

  if (!report?.report) {
    return (
      <ConsumerPageShell>
        <ConsumerHero
          eyebrow="Разбор"
          title="Отчет не найден"
          description="Этот разбор еще не готов или уже недоступен в текущем сценарии."
          status={
            <ConsumerStatusBadge label="Нет содержимого" description="Проверьте историю отчетов" tone="slate" />
          }
        />
        <div className="mx-auto w-full max-w-md">
          <ConsumerPanel className="p-5">
            <EmptyState
              compact
              title="Отчет не найден"
              message="Этот разбор еще не готов или уже недоступен."
              actionLabel="К истории отчетов"
              actionHref="/reports/history"
            />
          </ConsumerPanel>
        </div>
      </ConsumerPageShell>
    );
  }

  if (report.report.status === "failed") {
    const failureContext = fetchFailureContext();
    return (
      <ConsumerPageShell contentClassName="gap-0 px-0 pb-24 pt-0 sm:px-0 sm:pt-0">
        {checkoutToken && (
          <div data-testid="read-resume-entry" className="px-4 pt-6 sm:px-6 sm:pt-8">
            <div className="mx-auto max-w-3xl">
              <CatalogCheckoutResumeBanner
                surface="read"
                entryPoint={READ_ENTRY_POINT}
                checkoutToken={checkoutToken}
                mockEnabled={isMockRoute}
                runtimeEnabled={runtimeEnabled}
                initData={effectiveInitData}
                isReady={isReady || isMockRoute}
                mode={effectiveMode}
                onTrackAction={handleResumeCTA}
              />
            </div>
          </div>
        )}
        <ConsumerHero
          eyebrow="Разбор"
          title={title}
          description="Сборка не завершилась, но сценарий можно перезапустить без потери контекста."
          status={
            <ConsumerStatusBadge
              label="Не удалось собрать"
              description="Попробуйте перегенерацию"
              tone="rose"
            />
          }
          meta={<ConsumerMetaPill label="Для" value={clientName} />}
        />
        <div className="mx-auto w-full max-w-md">
          <ConsumerPanel data-testid="report-failure-surface" data-grace-surface="failure" className="p-8 text-center">
            <section data-testid="report-failure-context" data-grace-block="FAILURE_CONTEXT" className="space-y-4">
              <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-rose-50 text-rose-400">
              <RefreshCw size={32} />
              </div>
              <h2 className="text-2xl font-black tracking-tight text-slate-800">Отчет не удалось собрать</h2>
              <p className="mt-3 text-sm leading-relaxed text-slate-500">
                Произошла ошибка при анализе данных. Попробуйте запустить генерацию снова, это бесплатно.
              </p>
              <p data-testid="report-failure-meta" className="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
                {failureContext.report_type} • {failureContext.entry_point}
              </p>
            </section>
            <section data-testid="report-failure-retry-block" data-grace-block="FAILURE_RETRY" className="mt-8">
              <button
                onClick={handleRetry}
                data-testid="read-regenerate-button"
                className="flex w-full items-center justify-center gap-2 rounded-[22px] bg-slate-900 py-4 font-bold text-white shadow-lg shadow-slate-200"
              >
                <RefreshCw size={20} />
                Перегенерировать
              </button>
            </section>
            <section data-testid="report-failure-support-block" data-grace-block="FAILURE_SUPPORT" className="mt-6">
              <Link
                href="/reports/history"
                onClick={handleSupportCTA}
                data-testid="read-failure-history-link"
                className="inline-flex text-sm font-bold text-slate-400 transition-colors hover:text-slate-600"
              >
                Вернуться в историю
              </Link>
            </section>
          </ConsumerPanel>
        </div>
      </ConsumerPageShell>
    );
  }

  return (
    <ConsumerPageShell contentClassName="gap-0 px-0 pb-24 pt-0 sm:px-0 sm:pt-0">
      <div data-testid="read-sticky-panel" className="sticky top-0 z-20 border-b border-white/70 bg-white/78 px-4 py-3 shadow-sm shadow-slate-100/70 backdrop-blur-xl sm:px-6">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-3">
          <Link
            href="/reports/history"
            aria-label="К истории отчетов"
            className="flex h-10 w-10 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
          >
            <ArrowLeft size={22} strokeWidth={1.8} />
          </Link>
          <div className="min-w-0 text-center">
            <p className="text-[10px] font-black uppercase tracking-[0.22em] text-slate-400">Разбор</p>
            <h1 className="truncate text-sm font-black text-slate-800">{title}</h1>
          </div>
          <div className="w-10" />
        </div>
      </div>

      <div className="px-4 py-6 sm:px-6 sm:py-8">
        <div className="mx-auto max-w-3xl space-y-5">
          {checkoutToken && (
            <div data-testid="read-resume-entry"><CatalogCheckoutResumeBanner
                surface="read"
                entryPoint={READ_ENTRY_POINT}
                checkoutToken={checkoutToken}
                mockEnabled={isMockRoute}
                runtimeEnabled={runtimeEnabled}
                initData={effectiveInitData}
                isReady={isReady || isMockRoute}
                mode={effectiveMode}
                onTrackAction={handleResumeCTA}
              />
            </div>
          )}

          <ConsumerHero
            eyebrow="Разбор"
            title={title}
            description={buildReadDescription(reportStatus, clientName, sections.length)}
            status={
              <ConsumerStatusBadge
                label={statusMeta.label}
                description={statusMeta.description}
                tone={statusMeta.tone}
              />
            }
            meta={
              <>
                <ConsumerMetaPill label="Для" value={clientName} />
                {accessSource && (
                  <ConsumerMetaPill label="Доступ" value={formatAccessSource(accessSource)} />
                )}
                <ConsumerMetaPill
                  label="Секций"
                  value={reportStatus === "completed" ? String(sections.length) : statusMeta.metaValue}
                />
                <ConsumerMetaPill
                  label="Чтение"
                  value={reportStatus === "completed" ? `~${formatReadingTime(totalReadingMinutes)}` : "После генерации"}
                />
                {continuitySummary && (
                  <ConsumerMetaPill label={continuitySummary.label} value={continuitySummary.value} />
                )}
              </>
            }
            actions={
              reportStatus === "completed" && sections.length > 1 ? (
                <button
                  onClick={toggleAllSections}
                  className="rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 shadow-sm transition-colors hover:bg-slate-50"
                >
                  {allSectionsExpanded ? "Свернуть все" : "Раскрыть все"}
                </button>
              ) : null
            }
          />

          {continuitySummary && continuityEvidence.length > 0 && (
            <ConsumerPanel data-testid="read-known-time-panel" className="p-4 sm:p-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Known-time continuity</p>
                  <h2 className="mt-2 text-lg font-black tracking-tight text-slate-900">Сценарий чтения держится на точном времени рождения</h2>
                  <p data-testid="read-known-time-summary" className="mt-2 text-sm leading-relaxed text-slate-500">
                    Экран сохраняет majority-path continuity для точного времени, чтобы Today, Week и Read опирались на один и тот же временной контур.
                  </p>
                </div>
                <div data-testid="read-known-time-evidence" className="rounded-[24px] border border-indigo-100 bg-indigo-50/80 px-4 py-3 text-sm font-semibold text-indigo-900">
                  {continuityEvidence.join(" • ")}
                </div>
              </div>
            </ConsumerPanel>
          )}

          {sections.length > 0 && (
            <ConsumerPanel data-testid="read-overview-panel" className="p-4 sm:p-5">
              <div className="flex items-start gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 shadow-sm">
                  <ListChecks size={20} />
                </div>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Навигация по разбору</p>
                    <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.16em] text-slate-500">
                      Открыто {openedCount} из {sections.length}
                    </span>
                  </div>
                  <h2 className="mt-2 text-lg font-black tracking-tight text-slate-900">
                    Сначала выберите нужный блок, а не читайте весь отчет подряд
                  </h2>
                  <p className="mt-2 text-sm leading-relaxed text-slate-500">
                    Превью и оценка времени помогают быстро войти в тему. Начните с секции, которая ближе к вашей задаче, и возвращайтесь к остальным по мере необходимости.
                  </p>
                </div>
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <article className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                  <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Шаг 1</p>
                  <p className="mt-2 text-sm font-black text-slate-900">Сверьтесь с превью</p>
                  <p className="mt-2 text-sm leading-relaxed text-slate-500">
                    Короткое описание секции показывает, о чём блок и зачем в него заходить.
                  </p>
                </article>
                <article className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                  <div className="flex items-center gap-2">
                    <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Шаг 2</p>
                    <Clock3 size={14} className="text-slate-400" />
                  </div>
                  <p className="mt-2 text-sm font-black text-slate-900">Ориентируйтесь по времени</p>
                  <p className="mt-2 text-sm leading-relaxed text-slate-500">
                    У каждой секции есть оценка чтения, чтобы проще выбрать быстрый проход или полный разбор.
                  </p>
                </article>
                <article className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                  <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Шаг 3</p>
                  <p className="mt-2 text-sm font-black text-slate-900">Раскрывайте все только при сравнении</p>
                  <p className="mt-2 text-sm leading-relaxed text-slate-500">
                    Кнопка выше нужна для сквозного чтения. В обычном сценарии точечное раскрытие воспринимается легче.
                  </p>
                </article>
              </div>

              <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
                {sections.map((section, index) => (
                  <a
                    key={section.id}
                    href={`#${section.anchorId}`}
                    className="min-w-[220px] rounded-[22px] border border-slate-200 bg-white px-4 py-3 shadow-sm transition-colors hover:border-indigo-200 hover:bg-indigo-50/40"
                  >
                    <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
                      Секция {String(index + 1).padStart(2, "0")} • {formatReadingTime(section.readingMinutes)}
                    </p>
                    <p className="mt-2 text-sm font-black leading-snug text-slate-900">{section.title}</p>
                    <p className="mt-2 text-sm leading-relaxed text-slate-500">
                      {section.preview || "Откройте секцию, чтобы посмотреть содержание целиком."}
                    </p>
                  </a>
                ))}
              </div>
            </ConsumerPanel>
          )}

          <ConsumerPanel data-testid="read-share-section" className="p-4 sm:p-6">
            {/* START_BLOCK: SHARE_SECTION */}
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Поделиться</p>
                <h2 className="mt-2 text-lg font-black tracking-tight text-slate-900">Отправьте ссылку на разбор без потери контекста</h2>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">
                  Внешний вид и структура чтения сохраняются. Если кнопка share недоступна, ссылка просто скопируется.
                </p>
              </div>
              <button
                type="button"
                onClick={handleShare}
                data-testid="read-share-button"
                className="rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 shadow-sm transition-colors hover:bg-slate-50"
              >
                Поделиться разбором
              </button>
            </div>
            {/* END_BLOCK: SHARE_SECTION */}
          </ConsumerPanel>

          {chartSvg && (
            <ConsumerPanel className="overflow-hidden p-4 sm:p-6">
              <div className="space-y-4">
                <div>
                  <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Опорная карта</p>
                  <h2 className="mt-2 text-lg font-black tracking-tight text-slate-900">Визуальная схема для сверки с текстом</h2>
                  <p className="mt-2 text-sm leading-relaxed text-slate-500">
                    Если хотите сопоставить выводы с астрологической картой, держите схему рядом с текстовыми секциями.
                  </p>
                </div>

                <div className="flex justify-center">
                  <div
                    className="chart-svg-container aspect-square w-full max-w-[500px]"
                    dangerouslySetInnerHTML={{ __html: chartSvg }}
                  />
                </div>
              </div>
            </ConsumerPanel>
          )}

          {showPendingState && (
            <ConsumerPanel data-testid="read-pending-state" className="py-16 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-slate-500">
                <RefreshCw className="animate-spin" size={32} />
              </div>
              <h3 className="mt-6 text-lg font-bold text-slate-800">Готовим отчет...</h3>
              <p className="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-slate-500">
                Анализ карты занимает 1-2 минуты. Экран можно оставить открытым.
              </p>
            </ConsumerPanel>
          )}

          {showEmptyState && (
            <ConsumerPanel data-testid="report-empty-state" className="p-6">
              <EmptyState
                title="В отчете пока нет доступных блоков"
                message="Мы получили пустой или неполный ответ. Попробуйте открыть разбор позже или запустить перегенерацию."
                actionLabel="К истории отчетов"
                actionHref="/reports/history"
              />
            </ConsumerPanel>
          )}

          <div className="space-y-4">
            {sections.map((section, index) => {
              const isExpanded = expandedSections[section.id];
              const showsFallbackOnly = section.blocks.length === 0 && section.fallbackText;

              return (
                <div key={section.id} data-testid={`read-section-${section.id}`}>
                  <ForecastSectionCard
                    index={index + 1}
                    anchorId={section.anchorId}
                    title={section.title}
                    preview={section.preview}
                    meta={`Секция ${String(index + 1).padStart(2, "0")} • ${formatReadingTime(section.readingMinutes)}`}
                    expanded={Boolean(isExpanded)}
                    onToggle={() => toggleSection(section.id)}
                    badge={showsFallbackOnly ? "Текстовый режим" : null}
                  >
                    <ReportRenderer
                      blocks={section.blocks}
                      fallbackText={section.fallbackText}
                      fallbackTitle="Секция сохранена в упрощенном виде"
                    />
                  </ForecastSectionCard>
                </div>
              );
            })}
          </div>

          <div className="pt-4 text-center text-xs font-medium uppercase tracking-[0.28em] text-slate-400">
            <p>AstroSaaS © 2026</p>
            <p className="mt-2 opacity-60">ID: {report.report.id || reportId}</p>
          </div>
        </div>
      </div>

      <MicroFeedback reportId={reportId} />
    </ConsumerPageShell>
  );
}

export default function ReadReportPage() {
  return (
    <Suspense fallback={<ConsumerPageShell testId="read-page"><ConsumerPanel className="p-5"><LoadingState compact message="Загружаем разбор..." /></ConsumerPanel></ConsumerPageShell>}>
      <ReadReportPageContent />
    </Suspense>
  );
}
