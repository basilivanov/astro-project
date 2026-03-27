"use client";

import { useEffect, useRef, type ComponentPropsWithoutRef, type ReactNode } from "react";
import { CorrelationManager } from "../lib/correlation";
import { cn } from "../lib/utils";
import { trackCatalogEvent, type CatalogAnalyticsEvent } from "./catalog/catalog-analytics";
import { CATALOG_GRACE_MODULES, withCatalogTrace } from "./catalog/create-shared";

type StatusTone = "emerald" | "indigo" | "amber" | "rose" | "slate";

// START_MODULE_CONTRACT: M-CONSUMER-PAGE-SHELL
// purpose: Render reusable consumer-facing shell primitives with strict GRACE semantic blocks and canonical telemetry envelopes.
// owns:
//   - frontend/components/consumer-page-shell.tsx
// inputs:
//   - consumer shell props, analytics event metadata, semantic block/test ids
// outputs:
//   - branded shell/hero/panel/status/meta UI wrappers with stable semantic coordinates
// dependencies:
//   - frontend/components/catalog/catalog-analytics.ts
//   - frontend/components/catalog/create-shared.ts
//   - frontend/lib/correlation.ts
// side_effects:
//   - emits catalog telemetry for shell view impressions when analyticsEvent is provided
// invariants:
//   - exported primitives expose stable semantic wrappers for E2E and trace review
//   - shell analytics payloads include module, contract, block, semantic_block, correlation_id
// failure_policy:
//   - rendering degrades to visual shell output when analytics metadata is partial
// non_goals:
//   - page-specific business data mapping or copy generation
// END_MODULE_CONTRACT: M-CONSUMER-PAGE-SHELL

// START_MODULE_MAP: M-CONSUMER-PAGE-SHELL
// entrypoints:
//   - ConsumerPageShell
//   - ConsumerHero
//   - ConsumerPanel
//   - ConsumerStatusBadge
//   - ConsumerMetaPill
// owned_tests:
//   - frontend/e2e/core-ux.spec.ts
// adjacent_modules:
//   - frontend/app/page.tsx
//   - frontend/app/reports/history/page.tsx
//   - frontend/lib/home-analytics.ts
// END_MODULE_MAP: M-CONSUMER-PAGE-SHELL

const CONSUMER_SHELL_MODULE_ID = "M-CONSUMER-PAGE-SHELL";

const STATUS_TONE_CLASSES: Record<StatusTone, string> = {
  emerald: "border-emerald-100 bg-emerald-50 text-emerald-800",
  indigo: "border-indigo-100 bg-indigo-50 text-indigo-800",
  amber: "border-amber-100 bg-amber-50 text-amber-800",
  rose: "border-rose-100 bg-rose-50 text-rose-800",
  slate: "border-slate-200 bg-slate-50 text-slate-700",
};

export function ConsumerPageShell({
  children,
  className,
  contentClassName,
  testId,
  analyticsEvent,
}: {
  children: ReactNode;
  className?: string;
  contentClassName?: string;
  testId?: string;
  analyticsEvent?: CatalogAnalyticsEvent;
}) {
  // START_CONTRACT: FN-CONSUMER-PAGE-SHELL
  // purpose: Render the consumer shell wrapper and emit a canonical shell-view telemetry event once per mount.
  // inputs: children, css overrides, optional test id, optional analytics event metadata.
  // returns: consumer shell layout wrapper.
  // side_effects: dispatches a catalog analytics event enriched with GRACE trace coordinates.
  // error_behavior: skips telemetry when analytics metadata is absent.
  // END_CONTRACT: FN-CONSUMER-PAGE-SHELL
  const hasTrackedViewRef = useRef(false);

  useEffect(() => {
    if (!analyticsEvent || hasTrackedViewRef.current) {
      return;
    }
    // START_BLOCK: SHELL_TELEMETRY
    hasTrackedViewRef.current = true;
    const payload = withCatalogTrace(
      analyticsEvent.payload,
      {
        module:
          typeof analyticsEvent.payload?.module === "string"
            ? analyticsEvent.payload.module
            : CATALOG_GRACE_MODULES.homeFeed ?? CONSUMER_SHELL_MODULE_ID,
        contract:
          typeof analyticsEvent.payload?.contract === "string"
            ? analyticsEvent.payload.contract
            : "FN-CONSUMER-PAGE-SHELL",
        block:
          typeof analyticsEvent.payload?.block === "string"
            ? analyticsEvent.payload.block
            : "SHELL_RENDER",
        semantic_block:
          typeof analyticsEvent.payload?.semantic_block === "string"
            ? analyticsEvent.payload.semantic_block
            : typeof analyticsEvent.payload?.block === "string"
              ? analyticsEvent.payload.block
              : "SHELL_RENDER",
        correlation_id:
          typeof analyticsEvent.payload?.correlation_id === "string"
            ? analyticsEvent.payload.correlation_id
            : CorrelationManager.ensureCorrelationId(),
      },
    );
    void trackCatalogEvent(analyticsEvent.event_name, payload);
    // END_BLOCK: SHELL_TELEMETRY
  }, [analyticsEvent]);

  return (
    <div
      data-testid={testId ?? "consumer-page-shell"}
      data-block="SHELL_RENDER"
      data-semantic-block="SHELL_RENDER"
      data-module={CONSUMER_SHELL_MODULE_ID}
      className={cn(
        "min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(99,102,241,0.14),transparent_32%),radial-gradient(circle_at_top_right,rgba(251,191,36,0.12),transparent_22%),linear-gradient(180deg,#fffaf4_0%,#f8fafc_100%)]",
        className,
      )}
      suppressHydrationWarning
    >
      {/* START_BLOCK: SHELL_RENDER */}
      <div
        data-testid="consumer-page-shell-content"
        data-block="SHELL_CONTENT"
        data-semantic-block="SHELL_CONTENT"
        className={cn(
          "mx-auto flex min-h-screen max-w-3xl flex-col gap-5 px-4 pb-28 pt-6 sm:gap-6 sm:px-6 sm:pt-8",
          contentClassName,
        )}
      >
        {children}
      </div>
      {/* END_BLOCK: SHELL_RENDER */}
    </div>
  );
}

export function ConsumerStatusBadge({
  label,
  description,
  tone = "slate",
  className,
}: {
  label: string;
  description?: string;
  tone?: StatusTone;
  className?: string;
}) {
  // START_CONTRACT: FN-CONSUMER-STATUS-BADGE
  // purpose: Render a compact status badge with stable semantic hooks.
  // inputs: label, optional description, tone, className.
  // returns: stylized status badge element.
  // side_effects: none.
  // error_behavior: renders without description when omitted.
  // END_CONTRACT: FN-CONSUMER-STATUS-BADGE
  return (
    <div
      data-testid="consumer-status-badge"
      data-block="HERO_STATUS"
      data-semantic-block="HERO_STATUS"
      className={cn("rounded-[22px] border px-4 py-3 shadow-sm", STATUS_TONE_CLASSES[tone], className)}
    >
      {/* START_BLOCK: HERO_STATUS */}
      <p className="text-[10px] font-black uppercase tracking-[0.2em]">{label}</p>
      {description ? <p className="mt-1 text-sm font-semibold leading-snug">{description}</p> : null}
      {/* END_BLOCK: HERO_STATUS */}
    </div>
  );
}

export function ConsumerHero({
  eyebrow,
  title,
  description,
  status,
  meta,
  actions,
  className,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  status?: ReactNode;
  meta?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  // START_CONTRACT: FN-CONSUMER-HERO
  // purpose: Render the consumer hero surface with semantic slots for status, meta, and actions.
  // inputs: eyebrow, title, description, optional status/meta/actions nodes, className.
  // returns: branded hero header.
  // side_effects: none.
  // error_behavior: omits optional sections when no content is provided.
  // END_CONTRACT: FN-CONSUMER-HERO
  return (
    <header
      data-testid="consumer-hero"
      data-block="HERO_RENDER"
      data-semantic-block="HERO_RENDER"
      className={cn(
        "relative overflow-hidden rounded-[32px] border border-white/70 bg-white/88 px-5 py-5 shadow-[0_24px_60px_-32px_rgba(15,23,42,0.35)] backdrop-blur-xl",
        className,
      )}
    >
      <div className="pointer-events-none absolute inset-x-10 top-0 h-px bg-gradient-to-r from-transparent via-indigo-200/90 to-transparent" />
      <div className="pointer-events-none absolute -right-10 top-0 h-28 w-28 rounded-full bg-indigo-100/80 blur-3xl" />
      <div className="pointer-events-none absolute -left-10 bottom-0 h-24 w-24 rounded-full bg-amber-100/80 blur-3xl" />

      <div className="relative">
        {/* START_BLOCK: HERO_CONTENT */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0">
            <p className="text-[11px] font-black uppercase tracking-[0.26em] text-indigo-700">{eyebrow}</p>
            <h1 className="mt-3 text-3xl font-black tracking-tight text-slate-950 sm:text-4xl">{title}</h1>
            {description ? (
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-slate-600 sm:text-[15px]">{description}</p>
            ) : null}
          </div>
          {status ? <div className="shrink-0" data-testid="consumer-hero-status" data-block="HERO_STATUS">{status}</div> : null}
        </div>

        {(meta || actions) && (
          <div className="mt-5 flex flex-col gap-3 border-t border-slate-100/90 pt-4 sm:flex-row sm:items-center sm:justify-between">
            {meta ? <div className="flex flex-wrap gap-2" data-testid="consumer-hero-meta" data-block="HERO_META">{meta}</div> : <div />}
            {actions ? <div className="flex flex-wrap gap-2" data-testid="consumer-hero-actions" data-block="HERO_ACTIONS">{actions}</div> : null}
          </div>
        )}
        {/* END_BLOCK: HERO_CONTENT */}
      </div>
    </header>
  );
}

export function ConsumerMetaPill({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  // START_CONTRACT: FN-CONSUMER-META-PILL
  // purpose: Render compact hero metadata with stable semantic selectors.
  // inputs: label, value, optional className.
  // returns: metadata pill element.
  // side_effects: none.
  // error_behavior: expects a displayable value string.
  // END_CONTRACT: FN-CONSUMER-META-PILL
  return (
    <div
      data-testid="consumer-meta-pill"
      data-block="HERO_META"
      data-semantic-block="HERO_META"
      className={cn(
        "rounded-2xl border border-slate-200/80 bg-slate-50/90 px-3 py-2 text-left shadow-sm",
        className,
      )}
    >
      {/* START_BLOCK: HERO_META */}
      <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">{label}</p>
      <p className="mt-1 text-sm font-semibold text-slate-700">{value}</p>
      {/* END_BLOCK: HERO_META */}
    </div>
  );
}

export function ConsumerPanel({
  children,
  className,
  ...props
}: ComponentPropsWithoutRef<"section"> & {
  children: ReactNode;
}) {
  // START_CONTRACT: FN-CONSUMER-PANEL
  // purpose: Render a reusable consumer content panel with stable semantic hooks.
  // inputs: section props, children.
  // returns: stylized section wrapper.
  // side_effects: none.
  // error_behavior: forwards native section props unchanged.
  // END_CONTRACT: FN-CONSUMER-PANEL
  return (
    <section
      data-testid={props["data-testid"] ?? "consumer-panel"}
      data-block={typeof props["data-block"] === "string" ? props["data-block"] : "PANEL_CONTENT"}
      data-semantic-block={typeof props["data-block"] === "string" ? props["data-block"] : "PANEL_CONTENT"}
      {...props}
      className={cn(
        "rounded-[28px] border border-white/70 bg-white/90 shadow-[0_24px_60px_-36px_rgba(15,23,42,0.28)] backdrop-blur-xl",
        className,
      )}
    >
      {/* START_BLOCK: PANEL_CONTENT */}
      {children}
      {/* END_BLOCK: PANEL_CONTENT */}
    </section>
  );
}
