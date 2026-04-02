// ############################################################################
// AI_HEADER: MODULE_READ_REPORT_ACTIONS
// ROLE: Build read page action handlers while preserving telemetry and behavior.
// DEPENDENCIES: catalog analytics, correlated fetch, browser share/clipboard APIs.
// ############################################################################

import {
  CATALOG_GRACE_MODULES,
  withCatalogTrace,
} from "../../../components/catalog/create-shared";
import { correlatedFetch } from "../../../lib/correlated-fetch";
import { toErrorMessage } from "../../../lib/report-loader";
import {
  FAILURE_FLOW_ID,
  READ_BLOCKS,
  READ_DIRECT_ENTRY_POINT,
  READ_ENTRY_POINT,
  type ReadFailureContext,
} from "./page-helpers";

export type CorrelateContext = {
  correlationId: string;
  flowId: string;
  block: string;
};

type TrackReadEvent = (
  eventName: string,
  payload: Record<string, unknown>,
  semantic?: Record<string, unknown>,
) => Promise<void> | void;

type TrackCatalogEvent = (
  eventName: string,
  payload: Record<string, unknown>,
  context: CorrelateContext,
) => void;

export function buildShareAction({
  reportId,
  shareUrl,
  setError,
  trackReadEvent,
}: {
  reportId: string;
  shareUrl: string;
  setError: (message: string) => void;
  trackReadEvent: TrackReadEvent;
}) {
  return async () => {
    try {
      await trackReadEvent(
        "catalog.read_share_click",
        { report_id: reportId, entry_point: READ_DIRECT_ENTRY_POINT, action: "share" },
        { contract: "FN-HANDLE-SHARE", block: READ_BLOCKS.shareSection },
      );

      if (navigator.share) {
        await navigator.share({ url: shareUrl });
        return;
      }

      await navigator.clipboard.writeText(shareUrl);
    } catch (shareError) {
      if (shareError instanceof Error && shareError.name === "AbortError") {
        return;
      }
      setError(toErrorMessage(shareError, "Не удалось поделиться разбором"));
    }
  };
}

export function buildResumeActionHandler({
  reportId,
  reportType,
  trackReadEvent,
}: {
  reportId: string;
  reportType?: string;
  trackReadEvent: TrackReadEvent;
}) {
  return (action: string, entryPoint = READ_ENTRY_POINT) => {
    void trackReadEvent(
      `catalog.read_${action}`,
      {
        report_id: reportId,
        report_type: reportType || "unknown",
        entry_point: entryPoint,
        action,
      },
      {
        contract: "FN-HANDLE-RESUME-CTA",
        block: READ_BLOCKS.resumeEntry,
      },
    );
  };
}

export function buildRetryAction({
  effectiveInitData,
  reportId,
  fetchFailureContext,
  onTrackCatalogEvent,
  onSuccess,
  onError,
}: {
  effectiveInitData: string | null;
  reportId: string;
  fetchFailureContext: () => ReadFailureContext;
  onTrackCatalogEvent: TrackCatalogEvent;
  onSuccess: () => void;
  onError: (message: string) => void;
}) {
  return async () => {
    if (!effectiveInitData || !reportId) return;
    const failureContext = fetchFailureContext();
    try {
      onTrackCatalogEvent(
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
            correlation_id: correlate(READ_BLOCKS.failureRetry, FAILURE_FLOW_ID).correlationId,
          },
        ),
        correlate(READ_BLOCKS.failureRetry, FAILURE_FLOW_ID),
      );

      const res = await correlatedFetch(
        `/api/reports/${reportId}/regenerate`,
        {
          method: "POST",
          headers: {
            "X-Telegram-Auth": effectiveInitData,
          },
        },
        correlate(READ_BLOCKS.failureRetry, FAILURE_FLOW_ID),
      );
      if (!res.ok) throw new Error("Не удалось запустить перегенерацию");
      onSuccess();
    } catch (regenerateError) {
      onError(toErrorMessage(regenerateError, "Не удалось запустить перегенерацию"));
    }
  };
}

export function buildSupportAction({
  fetchFailureContext,
  onTrackCatalogEvent,
}: {
  fetchFailureContext: () => ReadFailureContext;
  onTrackCatalogEvent: TrackCatalogEvent;
}) {
  return () => {
    const failureContext = fetchFailureContext();
    onTrackCatalogEvent(
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
          correlation_id: correlate(READ_BLOCKS.failureSupport, FAILURE_FLOW_ID).correlationId,
        },
      ),
      correlate(READ_BLOCKS.failureSupport, FAILURE_FLOW_ID),
    );
  };
}
