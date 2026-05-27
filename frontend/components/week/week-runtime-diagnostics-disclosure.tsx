"use client";

import { useEffect, useState } from "react";

import { isProductionRuntimeEnvironment, type TelegramBootstrapOutcome, type TelegramMode } from "../../lib/telegram-runtime";

const TOGGLE_EVENT_NAME = "astro:week-dev-indicator-toggle-request";

type WeekRuntimeDiagnosticsDisclosureProps = {
  renderPath?: string | null;
  bootstrapOutcome?: TelegramBootstrapOutcome["kind"] | null;
  mode?: TelegramMode | null;
};

function toDisplayValue(value: string | null | undefined, fallback: string) {
  if (typeof value !== "string") {
    return fallback;
  }
  const trimmed = value.trim();
  return trimmed ? trimmed : fallback;
}

export function WeekRuntimeDiagnosticsDisclosure({
  renderPath,
  bootstrapOutcome,
  mode,
}: WeekRuntimeDiagnosticsDisclosureProps) {
  const isProductionRuntime = isProductionRuntimeEnvironment();
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (isProductionRuntime) {
      return;
    }

    const handleToggle = () => {
      setExpanded((current) => !current);
    };

    window.addEventListener(TOGGLE_EVENT_NAME, handleToggle);
    return () => window.removeEventListener(TOGGLE_EVENT_NAME, handleToggle);
  }, [isProductionRuntime]);

  if (isProductionRuntime || !expanded) {
    return null;
  }

  return (
    <aside
      data-testid="week-runtime-diagnostics-disclosure"
      className="fixed right-2 top-8 z-40 w-[min(13rem,calc(100vw-1rem))] rounded-2xl border border-slate-200/80 bg-white/90 px-3 py-2 text-[11px] text-slate-700 shadow-[0_18px_45px_-28px_rgba(15,23,42,0.65)] backdrop-blur-sm"
      aria-live="polite"
    >
      <dl className="space-y-2">
        <div>
          <dt className="font-semibold uppercase tracking-[0.14em] text-slate-400">Render path</dt>
          <dd data-testid="week-runtime-diagnostics-render-path" className="mt-0.5 font-medium text-slate-900">
            {toDisplayValue(renderPath, "unknown")}
          </dd>
        </div>
        <div>
          <dt className="font-semibold uppercase tracking-[0.14em] text-slate-400">Bootstrap</dt>
          <dd data-testid="week-runtime-diagnostics-bootstrap" className="mt-0.5 font-medium text-slate-900">
            {toDisplayValue(bootstrapOutcome, "unknown")}
          </dd>
        </div>
        <div>
          <dt className="font-semibold uppercase tracking-[0.14em] text-slate-400">Mode</dt>
          <dd data-testid="week-runtime-diagnostics-mode" className="mt-0.5 font-medium text-slate-900">
            {toDisplayValue(mode, "unavailable")}
          </dd>
        </div>
      </dl>
    </aside>
  );
}
