"use client";

import { ConsumerPanel } from "../consumer-page-shell";
import { type WeekSurfaceModel } from "../../lib/week-brief";

export function WeekExplainabilityPanel({ week }: { week: WeekSurfaceModel }) {
  return (
    <ConsumerPanel className="p-5" data-testid="week-explainability-panel">
      <div className="space-y-4">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Почему карта именно такая</p>
          <h2 className="mt-2 text-lg font-black text-slate-950">Объяснимость</h2>
        </div>
        <div className="flex flex-wrap gap-2" data-testid="week-explainability-chips">
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">Уверенность: {typeof week.explainability.confidence === "number" ? `${Math.round(week.explainability.confidence * 100)}%` : "—"}</span>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">Факторов: {week.explainability.factor_count ?? 0}</span>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">Время рождения: {week.explainability.birth_time_used ? "точное" : "без точного времени"}</span>
          {week.explainability.top_signal_source ? <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">Источник: {week.explainability.top_signal_source}</span> : null}
        </div>
        {week.factors.length ? (
          <div className="grid gap-3">
            {week.factors.map((factor, index) => (
              <div key={factor.id ?? index} className="rounded-2xl border border-slate-100 bg-white/80 p-4" data-testid={`week-factor-${index + 1}`}>
                <p className="text-sm font-bold text-slate-900">{factor.label}</p>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">{factor.explanation_human ?? factor.explanation_astro ?? ""}</p>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </ConsumerPanel>
  );
}
