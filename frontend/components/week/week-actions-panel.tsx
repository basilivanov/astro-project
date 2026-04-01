"use client";

import { useState } from "react";

import { ConsumerPanel } from "../consumer-page-shell";
import { type WeekSurfaceModel } from "../../lib/week-brief";

function supportingFactors(week: WeekSurfaceModel, factorId?: string | null) {
  if (factorId) {
    const exact = week.factors.filter((factor) => factor.id === factorId);
    if (exact.length) return exact.slice(0, 2);
  }
  return week.factors.slice(0, 2);
}

function itemSupportingFactors(week: WeekSurfaceModel, item: WeekSurfaceModel["actions"][number]) {
  if (item.supporting_factors?.length) {
    return item.supporting_factors;
  }
  return supportingFactors(week, item.factor_id);
}

function renderItems(items: WeekSurfaceModel["actions"], testId: string, week: WeekSurfaceModel, kind: "action" | "risk") {
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <ul className="space-y-2" data-testid={testId}>
      {items.map((item, index) => (
        <li key={item.id ?? item.text} className="rounded-2xl border border-slate-100 bg-slate-50/70 px-4 py-3 text-sm leading-relaxed text-slate-700">
          <p>{item.text}</p>
          {item.why_text || itemSupportingFactors(week, item).length ? (
            <div className="mt-3 rounded-2xl border border-slate-100 bg-white/80 p-3" data-testid={`${testId}-explainability-${index + 1}`}>
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-bold text-slate-700">{kind === "risk" ? "Почему это важно" : "Почему это в фокусе"}</p>
                <button
                  type="button"
                  onClick={() => setOpenId((current) => (current === (item.id ?? `${index}`) ? null : (item.id ?? `${index}`)))}
                  className="text-[11px] font-bold text-slate-500 transition-colors hover:text-slate-800"
                  data-testid={`${testId}-explainability-toggle-${index + 1}`}
                >
                  {openId === (item.id ?? `${index}`) ? "Скрыть" : "Открыть"}
                </button>
              </div>
              <div className="mt-2 space-y-2" hidden={openId !== (item.id ?? `${index}`)}>
                {item.why_text ? <p className="text-xs leading-relaxed text-slate-600">{item.why_text}</p> : null}
                {itemSupportingFactors(week, item).map((factor, factorIndex) => (
                  <div key={factor.id ?? factorIndex} className="rounded-2xl bg-slate-50 px-3 py-2">
                    <p className="text-xs font-bold text-slate-900">{factor.label}</p>
                    <p className="mt-1 text-xs leading-relaxed text-slate-600">{factor.explanation_human ?? factor.explanation_astro ?? "Фактор поддерживает эту рекомендацию недели."}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

export function WeekActionsPanel({ week }: { week: WeekSurfaceModel }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <ConsumerPanel className="p-5" data-testid="week-actions-panel">
        <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Действия</p>
        <h2 className="mt-2 text-lg font-black text-slate-950">Что делать на этой неделе</h2>
        <div className="mt-4">{renderItems(week.actions, "week-actions-list", week, "action")}</div>
      </ConsumerPanel>
      <ConsumerPanel className="p-5" data-testid="week-risks-panel">
        <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Риски</p>
        <h2 className="mt-2 text-lg font-black text-slate-950">Что держать под контролем</h2>
        <div className="mt-4">{renderItems(week.risks, "week-risks-list", week, "risk")}</div>
      </ConsumerPanel>
    </div>
  );
}
