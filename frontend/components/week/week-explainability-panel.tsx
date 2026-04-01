"use client";

import { useId, useState } from "react";

import { ConsumerPanel } from "../consumer-page-shell";
import { type WeekSurfaceModel } from "../../lib/week-brief";

export function WeekExplainabilityPanel({ week }: { week: WeekSurfaceModel }) {
  const [isOpen, setIsOpen] = useState(false);
  const detailsId = useId();
  const confidencePercent = typeof week.explainability.confidence === "number" ? `${Math.round(week.explainability.confidence * 100)}%` : "—";
  const hasExplainabilityDetails =
    Boolean(week.factors.length) ||
    typeof week.explainability.factor_count === "number" ||
    Boolean(week.confidenceLabel) ||
    Boolean(week.birthTimeLabel) ||
    Boolean(week.topSignalLabel);

  return (
    <ConsumerPanel className="p-5" data-testid="week-explainability-panel">
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Почему карта именно такая</p>
            <h2 className="mt-2 text-lg font-black text-slate-950">Объяснимость</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600" data-testid="week-explainability-summary">
              {week.confidenceLabel ? `${week.confidenceLabel}. ` : ""}
              {week.birthTimeLabel.charAt(0).toUpperCase() + week.birthTimeLabel.slice(1)}.
              {week.topSignalLabel ? ` Главный слой влияния: ${week.topSignalLabel}.` : ""}
            </p>
          </div>
          {hasExplainabilityDetails ? (
            <button
              type="button"
              className="inline-flex shrink-0 items-center gap-2 rounded-full border border-slate-200 px-3 py-2 text-xs font-bold text-slate-700 transition-colors hover:border-slate-300 hover:text-slate-900"
              aria-expanded={isOpen}
              aria-controls={detailsId}
              data-testid="week-explainability-toggle"
              onClick={() => setIsOpen((value) => !value)}
            >
              {isOpen ? "Свернуть детали" : "Открыть детали"}
            </button>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2" data-testid="week-explainability-chips">
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">Уверенность: {confidencePercent}</span>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">Опора: {week.confidenceShortLabel ?? "—"}</span>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">Факторов: {week.explainability.factor_count ?? week.factors.length}</span>
        </div>
        {hasExplainabilityDetails ? (
          <div
            id={detailsId}
            hidden={!isOpen}
            aria-hidden={!isOpen}
            className="space-y-4"
            data-testid="week-explainability-details"
          >
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">Контекст: {week.birthTimeLabel}</span>
              {week.topSignalLabel ? <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">Основа: {week.topSignalLabel}</span> : null}
            </div>
            {week.factors.length ? (
              <div className="grid gap-3">
                {week.factors.map((factor, index) => (
                  <div key={factor.id ?? index} className="rounded-2xl border border-slate-100 bg-white/80 p-4" data-testid={`week-factor-${index + 1}`}>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-sm font-bold text-slate-900">{factor.label}</p>
                      {factor.impact ? (
                        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-slate-600" data-testid={`week-factor-impact-${index + 1}`}>
                          {factor.impact === "high" ? "Основной" : factor.impact === "medium" ? "Поддерживающий" : "Фоновый"}
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-1 text-xs leading-relaxed text-slate-600">{factor.explanation_human ?? factor.explanation_astro ?? ""}</p>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </ConsumerPanel>
  );
}
