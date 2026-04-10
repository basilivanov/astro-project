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
            <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Поддерживающий слой</p>
            <h2 className="mt-2 text-lg font-black text-slate-950">Почему неделя держится именно так</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600" data-testid="week-explainability-summary">
              {week.explainabilitySummary ?? [week.confidenceLabel, week.birthTimeLabel ? week.birthTimeLabel.charAt(0).toUpperCase() + week.birthTimeLabel.slice(1) : null, week.topSignalLabel ? `Главный слой влияния: ${week.topSignalLabel}` : null].filter(Boolean).join(". ") + "."}
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
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">Факторов в модели: {week.explainability.factor_count ?? week.factors.length}</span>
        </div>
        {hasExplainabilityDetails ? (
          <div
            id={detailsId}
            hidden={!isOpen}
            aria-hidden={!isOpen}
            className="space-y-4"
            data-testid="week-explainability-details"
          >
            <div className="grid gap-3 md:grid-cols-3" data-testid="week-explainability-top-layer">
              {(week.explainabilityDetailItems ?? []).map((item) => (
                <div key={item.id} className="rounded-2xl border border-slate-100 bg-white/80 p-4" data-testid={item.id}>
                  <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-400">{item.title}</p>
                  {item.value ? <p className="mt-2 text-sm font-bold text-slate-900">{item.value}</p> : null}
                  {item.body ? <p className="mt-2 text-xs leading-relaxed text-slate-600">{item.body}</p> : null}
                </div>
              ))}
            </div>
            <p className="text-xs leading-relaxed text-slate-500" data-testid="week-explainability-footnote">
              Ключевые причины уже встроены в домены недели через «Что повлияло». Здесь оставляем только слой доверия к интерпретации.
            </p>
          </div>
        ) : null}
      </div>
    </ConsumerPanel>
  );
}
