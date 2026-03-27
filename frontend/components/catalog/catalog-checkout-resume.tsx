"use client";

import { useEffect, useMemo, useRef, useState, type MouseEvent } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Loader2 } from "lucide-react";

import { CorrelationManager } from "../../lib/correlation";
import { cn } from "../../lib/utils";
import {
  type CatalogEventPayload,
  type CatalogSurface,
  setCatalogAnalyticsContext,
  startCatalogCorrelation,
  setCatalogCorrelationId,
  trackCatalogEvent,
} from "./catalog-analytics";
import { CATALOG_GRACE_BLOCKS, CATALOG_GRACE_MODULES, withCatalogTrace } from "./create-shared";

const REPORT_LABELS: Record<string, string> = {
  natal_master: "Натальная карта",
  month_forecast: "Прогноз на месяц",
  year_forecast: "Альманах",
  ten_year_forecast: "Прогноз на 10 лет",
  solar_return: "Соляр",
  synastry: "Совместимость",
  horary: "Вопрос",
  horary_answer: "Вопрос",
  week_forecast: "Прогноз на неделю",
};

type CheckoutSession = {
  status?: string;
  report_type?: string | null;
  resumed_report_id?: string | null;
  return_path?: string | null;
};

type ResumeStatus =
  | "checking"
  | "pending"
  | "succeeded"
  | "canceled"
  | "failed"
  | "unauthorized"
  | "error";

type Tone = "info" | "success" | "warning" | "error";

const TONE_MAP: Record<Tone, string> = {
  info: "border-indigo-100 bg-indigo-50/80 text-indigo-900",
  success: "border-emerald-100 bg-emerald-50/80 text-emerald-900",
  warning: "border-amber-100 bg-amber-50/80 text-amber-900",
  error: "border-rose-100 bg-rose-50/80 text-rose-900",
};

// START_MODULE_CONTRACT: M-CATALOG-CHECKOUT-RESUME
// purpose: Surface inline CTA + status for resuming catalog checkout tokens in client runtime.
// owns:
//   - frontend/components/catalog/catalog-checkout-resume.tsx
// inputs:
//   - checkoutToken from query params, Telegram init data, runtime flags
// outputs:
//   - CTA UI, telemetry events (catalog.checkout_resume_*)
// dependencies:
//   - catalog-analytics helpers for correlation and trackEvent
//   - Next.js navigation for cancel flows
// side_effects:
//   - fetches billing checkout session state from `/api/billing/sessions/:token`
//   - updates analytics context/correlation and emits checkout resume telemetry
// invariants:
//   - stop polling once checkout result is final
//   - correlation id resets when checkout token changes
// failure_policy:
//   - render unauthorized/error copy when auth or session sync is unavailable
//   - keep CTA available with safe fallback href when return path is absent
// non_goals:
//   - Fetching billing session without auth or handling payment provider specifics
// END_MODULE_CONTRACT: M-CATALOG-CHECKOUT-RESUME

// START_MODULE_MAP: M-CATALOG-CHECKOUT-RESUME
// entrypoints:
//   - CatalogCheckoutResumeBanner (default export)
// key_flows:
//   - sync -> fetch session -> track block-aware telemetry
// owned_tests:
//   - frontend/e2e/billing-catalog-alignment.spec.ts
// adjacent_modules:
//   - frontend/app/create/create-page-client.tsx
//   - frontend/components/catalog/catalog-analytics.ts
// END_MODULE_MAP: M-CATALOG-CHECKOUT-RESUME

export function CatalogCheckoutResumeBanner({
  surface,
  entryPoint,
  checkoutToken,
  mockEnabled,
  runtimeEnabled,
  initData,
  isReady,
  mode,
  onTrackAction,
}: {
  surface: CatalogSurface;
  entryPoint?: string;
  checkoutToken: string | null;
  mockEnabled?: boolean;
  runtimeEnabled?: boolean;
  initData: string;
  isReady: boolean;
  mode: string;
  onTrackAction?: (action: string, entryPoint?: string) => void;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [session, setSession] = useState<CheckoutSession | null>(null);
  const [status, setStatus] = useState<ResumeStatus>("checking");
  const trackedTokenRef = useRef<string | null>(null);
  const statusTrackedRef = useRef<string | null>(null);
  const pollRef = useRef<number | null>(null);
  const touchStartXRef = useRef<number | null>(null);
  const shouldRender = Boolean(checkoutToken);
  const correlationId = useMemo(() => CorrelationManager.ensureCorrelationId(), []);

  // START_CONTRACT: FN-RESOLVE-REPORT-LABEL
  // purpose: Derive user-facing report label for resume copy.
  // inputs: current checkout session report_type.
  // returns: localized label string.
  // END_CONTRACT: FN-RESOLVE-REPORT-LABEL
  // START_BLOCK: TOKEN_RESOLUTION
  const reportLabel = useMemo(() => {
    if (session?.report_type && REPORT_LABELS[session.report_type]) {
      return REPORT_LABELS[session.report_type];
    }
    return "разбора";
  }, [session?.report_type]);
  // END_BLOCK: TOKEN_RESOLUTION

  // START_CONTRACT: FN-RESOLVE-RESUME-HREF
  // purpose: Build safe resume URL preserving mock/runtime flags.
  // inputs: checkout token, session return_path, runtime flags.
  // returns: resume href or null.
  // END_CONTRACT: FN-RESOLVE-RESUME-HREF
  // START_BLOCK: RESUME_LINK_STATE
  const resumeHref = useMemo(() => {
    if (!checkoutToken) {
      return null;
    }

    const basePath = session?.return_path || "/create";
    const url = new URL(basePath, "https://dummy.local");
    if (!url.searchParams.has("checkout")) {
      url.searchParams.set("checkout", checkoutToken);
    }
    if (mockEnabled || mode === "mock") {
      url.searchParams.set("mock", "1");
    }
    if (runtimeEnabled || mockEnabled || mode === "mock") {
      url.searchParams.set("runtime", "1");
    }
    return `${url.pathname}${url.search}`;
  }, [checkoutToken, mockEnabled, mode, runtimeEnabled, session?.return_path]);
  // END_BLOCK: RESUME_LINK_STATE

  // START_CONTRACT: FN-RESOLVE-CANCEL-HREF
  // purpose: Remove checkout marker from current route for safe cancel flow.
  // inputs: pathname + search params.
  // returns: next path without checkout query param.
  // END_CONTRACT: FN-RESOLVE-CANCEL-HREF
  const cancelHref = useMemo(() => {
    if (!searchParams) {
      return pathname;
    }
    const next = new URLSearchParams(searchParams.toString());
    next.delete("checkout");
    return next.toString() ? `${pathname}?${next.toString()}` : pathname;
  }, [pathname, searchParams]);

  const backHref = useMemo(() => {
    if (resumeHref) {
      return resumeHref;
    }
    return cancelHref || "/reports";
  }, [cancelHref, resumeHref]);

  useEffect(() => {
    if (!shouldRender) {
      return undefined;
    }

    const handleTouchStart = (event: TouchEvent) => {
      touchStartXRef.current = event.changedTouches[0]?.clientX ?? null;
    };

    const handleTouchEnd = (event: TouchEvent) => {
      const startX = touchStartXRef.current;
      const endX = event.changedTouches[0]?.clientX ?? null;
      touchStartXRef.current = null;
      if (startX === null || endX === null || endX - startX < 72) {
        return;
      }
      router.replace(backHref);
    };

    window.addEventListener("touchstart", handleTouchStart, { passive: true });
    window.addEventListener("touchend", handleTouchEnd, { passive: true });
    return () => {
      window.removeEventListener("touchstart", handleTouchStart);
      window.removeEventListener("touchend", handleTouchEnd);
    };
  }, [backHref, router, shouldRender]);

  // START_CONTRACT: FN-RESUME-BRIDGE
  // purpose: Bridge checkout token into shared correlation context and ready-state telemetry.
  // inputs: checkout token, entry point, surface.
  // side_effects: seeds analytics context + emits ready event once per token.
  // END_CONTRACT: FN-RESUME-BRIDGE
  useEffect(() => {
    if (!shouldRender || !checkoutToken) {
      if (trackedTokenRef.current) {
        trackedTokenRef.current = null;
        setCatalogAnalyticsContext({ checkout_token: undefined });
        setCatalogCorrelationId(null);
      }
      return;
    }
    if (trackedTokenRef.current === checkoutToken) {
      return;
    }
    trackedTokenRef.current = checkoutToken;
    statusTrackedRef.current = null;
    const correlationId = startCatalogCorrelation("catalog_checkout_resume");
    setCatalogAnalyticsContext({ checkout_token: checkoutToken, correlation_id: correlationId });
    // START_BLOCK: ANALYTICS_CONTEXT_BOOTSTRAP
    void trackCatalogEvent("catalog.checkout_resume_ready", withCatalogTrace({
      surface,
      entry_point: entryPoint ?? `${surface}-resume-banner`,
    }, {
      module: CATALOG_GRACE_MODULES.checkoutResume,
      contract: "FN-RESUME-BRIDGE",
      block: CATALOG_GRACE_BLOCKS.checkoutResume.ctaReady,
      correlation_id: correlationId,
    }));
    // END_BLOCK: ANALYTICS_CONTEXT_BOOTSTRAP
  }, [checkoutToken, entryPoint, shouldRender, surface]);

  // START_CONTRACT: FN-SYNC-RESUME-STATE
  // purpose: Load/poll checkout session state and emit correlation-aware telemetry.
  // inputs: checkout token, telegram auth, readiness flags.
  // side_effects:
  //   - fetches billing session state
  //   - updates local resume status/session
  //   - emits block-tagged analytics for transitions
  // invariants:
  //   - polling continues only while status is pending
  // END_CONTRACT: FN-SYNC-RESUME-STATE
  useEffect(() => {
    if (!shouldRender) {
      return undefined;
    }
    if (!isReady) {
      return undefined;
    }

    if (!initData) {
      setStatus("unauthorized");
      setSession(null);
      return undefined;
    }

    let cancelled = false;

    const trackSuccess = (reportType?: string | null) => {
      void trackCatalogEvent("catalog.checkout_resume_success", withCatalogTrace({
        surface,
        entry_point: entryPoint ?? `${surface}-resume-banner`,
        report_type: reportType ?? undefined,
      }, {
        module: CATALOG_GRACE_MODULES.checkoutResume,
        contract: "FN-CHECKOUT-RESUME-REFRESH",
        block: CATALOG_GRACE_BLOCKS.checkoutResume.resumeState,
        semantic_block: "CHECKOUT_RESUME_STATUS_SUCCEEDED",
        correlation_id: correlationId,
      }));
    };

    const sync = async () => {
      if (!checkoutToken) {
        return;
      }
      if (mockEnabled || mode === "mock") {
        const payload: CheckoutSession = {
          status: "succeeded",
          report_type: session?.report_type ?? "week_forecast",
        };
        setSession(payload);
        setStatus("succeeded");
        trackStatus("succeeded", {
          surface,
          entry_point: entryPoint ?? `${surface}-resume-banner`,
          report_type: payload.report_type ?? undefined,
          status: payload.status,
          correlation_id: correlationId,
        });
        trackSuccess(payload.report_type);
        return;
      }
      try {
        const response = await fetch(`/api/billing/sessions/${checkoutToken}`, {
          headers: { "X-Telegram-Auth": initData },
        });
        if (!response.ok) {
          throw new Error("checkout_session_unavailable");
        }
        const payload = (await response.json()) as CheckoutSession;
        if (cancelled) {
          return;
        }
        setSession(payload);
        const normalized = normalizeStatus(payload.status);
        setStatus(normalized);
        // START_BLOCK: RESUME_STATE
        trackStatus(normalized, {
          surface,
          entry_point: entryPoint ?? `${surface}-resume-banner`,
          report_type: payload.report_type ?? undefined,
          status: payload.status,
          correlation_id: correlationId,
        });
        // END_BLOCK: RESUME_STATE
        if (normalized === "pending") {
          pollRef.current = window.setTimeout(() => {
            void sync();
          }, 1500);
        }
        if (normalized === "succeeded") {
          trackSuccess(payload.report_type ?? undefined);
        }
      } catch (error) {
        if (!cancelled) {
          setStatus("error");
        }
      }
    };

    void sync();

    return () => {
      cancelled = true;
      if (pollRef.current) {
        window.clearTimeout(pollRef.current);
      }
    };
  }, [checkoutToken, correlationId, entryPoint, initData, isReady, mockEnabled, mode, session?.report_type, shouldRender, surface]);

  // START_FUNCTION_CONTRACT: FN-HANDLE-RESUME-CLICK
  // purpose: Track CTA tap before redirecting user to resume path.
  // side_effects:
  //   - emits `catalog.checkout_resume_start` telemetry
  // invariants:
  //   - no telemetry is sent when checkout token is missing
  // END_FUNCTION_CONTRACT: FN-HANDLE-RESUME-CLICK
  const handleResumeClick = () => {
    if (!checkoutToken) {
      return;
    }
    onTrackAction?.("resume_click", entryPoint ?? `${surface}-resume-banner`);
    // START_BLOCK: CTA_PRIMARY
    void trackCatalogEvent("catalog.checkout_resume_start", withCatalogTrace({
      surface,
      entry_point: entryPoint ?? `${surface}-resume-banner`,
      report_type: session?.report_type ?? undefined,
    }, {
      module: CATALOG_GRACE_MODULES.checkoutResume,
      contract: "FN-HANDLE-RESUME-CLICK",
      block: CATALOG_GRACE_BLOCKS.checkoutResume.ctaPrimary,
      semantic_block: "CHECKOUT_RESUME_CTA_PRIMARY",
      correlation_id: CorrelationManager.ensureCorrelationId(),
    }));
    // END_BLOCK: CTA_PRIMARY
  };

  // START_FUNCTION_CONTRACT: FN-HANDLE-CHECKOUT-CANCEL
  // purpose: Abandon checkout resume, clear correlation + analytics context.
  // side_effects:
  //   - emits cancel telemetry and clears analytics context
  //   - replaces current route without the `checkout` query param
  // invariants:
  //   - tracked token and status refs are reset before navigation
  // END_FUNCTION_CONTRACT: FN-HANDLE-CHECKOUT-CANCEL
  const handleCancel = (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    onTrackAction?.("resume_cancel", entryPoint ?? `${surface}-resume-banner`);
    // START_BLOCK: CTA_CANCEL
    void trackCatalogEvent("catalog.checkout_resume_cancel", withCatalogTrace({
      surface,
      entry_point: entryPoint ?? `${surface}-resume-banner`,
      report_type: session?.report_type ?? undefined,
    }, {
      module: CATALOG_GRACE_MODULES.checkoutResume,
      contract: "FN-HANDLE-CHECKOUT-CANCEL",
      block: CATALOG_GRACE_BLOCKS.checkoutResume.ctaCancel,
      semantic_block: "CHECKOUT_RESUME_CTA_CANCEL",
      correlation_id: CorrelationManager.ensureCorrelationId(),
    }));
    trackedTokenRef.current = null;
    statusTrackedRef.current = null;
    setCatalogAnalyticsContext({ checkout_token: undefined });
    router.replace(cancelHref);
    // END_BLOCK: CTA_CANCEL
  };

  if (!shouldRender) {
    return null;
  }

  const tone = getTone(status);
  const copy = buildCopy(status, reportLabel);

  return (
    <div
      data-testid="catalog-checkout-resume"
      className={cn(
        "rounded-3xl border px-4 py-4 text-sm font-medium shadow-sm sm:px-5 sm:py-5",
        TONE_MAP[tone],
      )}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-900/70">Активное оформление</p>
          {status === "checking" ? (
            <p className="mt-2 inline-flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" /> Проверяем платежную сессию…
            </p>
          ) : (
            <p className="mt-2 leading-relaxed">{copy}</p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-900/10 bg-white/90 px-4 py-2 text-sm font-semibold text-slate-900 shadow-sm transition hover:border-slate-900/30"
            onClick={() => router.replace(backHref)}
          >
            <ArrowLeft className="h-4 w-4" /> Назад
          </button>
          <Link
            href={resumeHref || "/create"}
            prefetch={false}
            className="inline-flex items-center justify-center rounded-2xl border border-slate-900/10 bg-white/90 px-4 py-2 text-sm font-semibold text-slate-900 shadow-sm transition hover:border-slate-900/30"
            onClick={handleResumeClick}
          >
            Вернуться
          </Link>
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-2xl border border-transparent bg-white/40 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-white/60"
            onClick={handleCancel}
          >
            Отменить
          </button>
        </div>
      </div>
    </div>
  );

  function normalizeStatus(value?: string | null): ResumeStatus {
    if (!value) {
      return "checking";
    }
    const map: Record<string, ResumeStatus> = {
      pending: "pending",
      created: "pending",
      succeeded: "succeeded",
      resumed: "succeeded",
      canceled: "canceled",
      failed: "failed",
    };
    return map[value] ?? "pending";
  }

  function getTone(current: ResumeStatus): Tone {
    if (current === "succeeded") {
      return "success";
    }
    if (current === "pending" || current === "checking") {
      return "info";
    }
    if (current === "canceled") {
      return "warning";
    }
    return "error";
  }

  function buildCopy(current: ResumeStatus, label: string) {
    switch (current) {
      case "pending":
        return `Продолжаем оформление ${label}. Вернуться к оплате?`;
      case "succeeded":
        return `${label} уже оплачен. Вернитесь, чтобы завершить запуск.`;
      case "canceled":
        return `Оформление ${label} отменено. Попробовать снова?`;
      case "failed":
        return `Оплата ${label} завершилась ошибкой. Попробуйте снова.`;
      case "unauthorized":
        return "Чтобы продолжить оформление, откройте экран из Telegram.";
      case "error":
        return "Не удалось проверить оплату. Повторите попытку.";
      default:
        return `Продолжаем оформление ${label}. Вернуться к оплате?`;
    }
  }

  // START_FUNCTION_CONTRACT: FN-TRACK-RESUME-STATUS
  // purpose: Emit telemetry for status transitions with block metadata.
  // side_effects:
  //   - sends `catalog.checkout_resume_status` event once per status value
  // invariants:
  //   - duplicate status transitions do not emit duplicate events
  // END_FUNCTION_CONTRACT: FN-TRACK-RESUME-STATUS
  function trackStatus(nextStatus: ResumeStatus, payload: CatalogEventPayload) {
    if (statusTrackedRef.current === nextStatus) {
      return;
    }
    statusTrackedRef.current = nextStatus;
    const block = `CHECKOUT_RESUME_STATUS_${nextStatus.toUpperCase()}`;
    void trackCatalogEvent("catalog.checkout_resume_status", withCatalogTrace({
      ...payload,
    }, {
      module: CATALOG_GRACE_MODULES.checkoutResume,
      contract: "FN-TRACK-RESUME-STATUS",
      block,
      correlation_id: typeof payload.correlation_id === "string" ? payload.correlation_id : null,
    }));
  }
}
