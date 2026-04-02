// ############################################################################
// AI_HEADER: MODULE_READ_REPORT_CONTROLLER
// ROLE: Own read report route state, data loading, telemetry context, and derived view model.
// DEPENDENCIES: Telegram runtime, route params, report fetch helpers, page helpers.
// ############################################################################

"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTelegram } from "../../../hooks/useTelegram";
import {
  FLOW_FORECAST_CATALOG,
  setCatalogAnalyticsContext,
  trackCatalogEvent,
} from "../../../components/catalog/catalog-analytics";
import { CATALOG_GRACE_MODULES } from "../../../components/catalog/create-shared";
import { correlatedFetch } from "../../../lib/correlated-fetch";
import { trackFrontend } from "../../../lib/frontend-observability";
import { loadReportById, toErrorMessage, type ReportResponse } from "../../../lib/report-loader";
import { formatReadingTime } from "../../../lib/forecast-ui";
import {
  buildExpandedSections,
  buildReadContinuityEvidence,
  buildReadContinuitySummary,
  buildReadDescription,
  buildReadFailureContext,
  extractReadContinuityFacts,
  prepareRenderableSections,
  READ_BLOCKS,
  READ_DIRECT_ENTRY_POINT,
  READ_ENTRY_POINT,
  READ_STATUS_META,
  type ReadFailureContext,
  type ReadContinuityFacts,
} from "./page-helpers";

export type ReadReportControllerResult = ReturnType<typeof useReadReportController>;

export function useReadReportController() {
  const params = useParams<{ id?: string | string[] }>();
  const searchParams = useSearchParams();
  const reportId = Array.isArray(params?.id) ? params.id[0] ?? "" : params?.id ?? "";
  const checkoutToken = searchParams.get("checkout_token");
  const isMockRoute = searchParams.get("mock") === "1";
  const runtimeEnabled = !isMockRoute;
  const shareUrl = typeof window === "undefined" ? "" : window.location.href;

  const { user, initData, isReady, mode } = useTelegram();
  const effectiveMode = isMockRoute ? "mock" : mode;
  const effectiveInitData = isMockRoute ? "mock-read-auth" : initData;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  const correlationIdRef = useRef<string | null>(null);

  const ensureCorrelationId = useCallback(() => {
    if (!correlationIdRef.current) {
      correlationIdRef.current = `${READ_ENTRY_POINT}:${reportId || "unknown"}:${Date.now()}`;
    }
    return correlationIdRef.current;
  }, [reportId]);

  const correlate = useCallback(
    (block: string, flowId = FLOW_FORECAST_CATALOG) => ({
      correlationId: ensureCorrelationId(),
      flowId,
      block,
    }),
    [ensureCorrelationId],
  );

  const trackReadEvent = useCallback(
    async (
      eventName: string,
      payload: Record<string, unknown>,
      semantic?: Record<string, unknown>,
    ) => {
      await trackFrontend(eventName, {
        module: CATALOG_GRACE_MODULES.readReport,
        correlation_id: ensureCorrelationId(),
        report_id: reportId,
        ...payload,
        ...semantic,
      });
    },
    [ensureCorrelationId, reportId],
  );

  const handleTrackCatalogEvent = useCallback(
    (eventName: string, payload: Record<string, unknown>, context: { correlationId: string; flowId: string; block: string }) => {
      void trackCatalogEvent(eventName, payload, {
        correlationId: context.correlationId,
        flowId: context.flowId,
        block: context.block,
      });
    },
    [],
  );

  const loadReport = useCallback(async () => {
    if (!reportId || (!effectiveInitData && !isMockRoute)) return;
    setLoading(true);
    setError("");

    try {
      const nextReport = await loadReportById({
        reportId,
        initData: effectiveInitData,
        isMockRoute,
        correlatedFetch,
        correlationId: ensureCorrelationId(),
      });
      setReport(nextReport);
    } catch (loadError) {
      setError(toErrorMessage(loadError, "Не удалось загрузить отчет"));
    } finally {
      setLoading(false);
    }
  }, [effectiveInitData, ensureCorrelationId, isMockRoute, reportId]);

  useEffect(() => {
    void loadReport();
  }, [loadReport]);

  const sections = useMemo(() => prepareRenderableSections(report?.report?.content), [report?.report?.content]);

  useEffect(() => {
    setExpandedSections(buildExpandedSections(sections));
  }, [sections]);

  const continuityFacts: ReadContinuityFacts = useMemo(() => extractReadContinuityFacts(report), [report]);

  const knownTimeContinuity = useMemo(() => {
    const summary = buildReadContinuitySummary(continuityFacts);
    const evidence = buildReadContinuityEvidence(continuityFacts);
    if (!summary && evidence.length === 0) {
      return null;
    }

    return {
      label: summary?.label ?? (continuityFacts.scenarioLabel === "whole-sign-edge" ? "Safe mode домов сохранён" : "Точное время сохранено"),
      value: summary?.value ?? (continuityFacts.scenarioLabel === "whole-sign-edge" ? "Safe mode: Whole Sign" : "Канонический known-time сценарий"),
      evidence,
    };
  }, [continuityFacts]);

  useEffect(() => {
    setCatalogAnalyticsContext({
      correlation_id: ensureCorrelationId(),
      entry_point: checkoutToken ? READ_ENTRY_POINT : READ_DIRECT_ENTRY_POINT,
      report_id: reportId || null,
      report_type: report?.report?.report_type || null,
      checkout_token: checkoutToken,
      fixture_id: continuityFacts.fixtureId,
      scenario_label: continuityFacts.scenarioLabel,
      manifest_id: continuityFacts.manifestId,
    });
  }, [checkoutToken, continuityFacts.fixtureId, continuityFacts.manifestId, continuityFacts.scenarioLabel, ensureCorrelationId, report?.report?.report_type, reportId]);

  const toggleSection = useCallback((sectionId: string) => {
    setExpandedSections((current) => ({
      ...current,
      [sectionId]: !current[sectionId],
    }));
  }, []);

  const status = report?.report?.status || "pending";
  const statusMeta = READ_STATUS_META[status] || READ_STATUS_META.pending;
  const clientName = report?.report?.person_name || user?.first_name || "клиента";
  const title = report?.report?.title || "Персональный разбор";
  const description = buildReadDescription(status, clientName, sections.length);
  const readingMinutes = Math.max(1, sections.reduce((sum, section) => sum + section.readingMinutes, 0));
  const readingTimeLabel = formatReadingTime(readingMinutes);
  const chartSvg = typeof report?.chart_svg === "string" ? report.chart_svg : null;
  const showPendingState = status === "pending" || status === "in_progress";
  const showEmptyState = !showPendingState && sections.length === 0;

  const fetchFailureContext = useCallback(
    (): ReadFailureContext =>
      buildReadFailureContext({
        reportId,
        reportType: report?.report?.report_type,
        status: report?.report?.status,
        hasCheckoutToken: Boolean(checkoutToken),
        readEntryPoint: READ_ENTRY_POINT,
        directEntryPoint: READ_DIRECT_ENTRY_POINT,
        failureSurface: "read_failure",
        failureFlowId: "catalog_read_failure",
      }),
    [checkoutToken, report?.report?.report_type, report?.report?.status, reportId],
  );

  const handleRetrySuccess = useCallback(() => {
    window.location.reload();
  }, []);

  return {
    chartSvg,
    checkoutToken,
    clientName,
    continuityFacts,
    correlate,
    description,
    effectiveInitData,
    effectiveMode,
    error,
    expandedSections,
    fetchFailureContext,
    handleRetrySuccess,
    handleTrackCatalogEvent,
    isMockRoute,
    isReady,
    loadReport,
    loading,
    knownTimeContinuity,
    readingTimeLabel,
    report,
    reportId,
    runtimeEnabled,
    sections,
    setError,
    shareUrl,
    showEmptyState,
    showPendingState,
    statusMeta,
    title,
    toggleSection,
    trackReadEvent,
  };
}
