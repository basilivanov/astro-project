"use client";

import { ConsumerPanel } from "../consumer-page-shell";
import { type WeekSurfaceModel } from "../../lib/week-brief";

function renderItems(items: WeekSurfaceModel["actions"], testId: string) {
  return (
    <ul className="space-y-2" data-testid={testId}>
      {items.map((item) => (
        <li key={item.id ?? item.text} className="rounded-2xl border border-slate-100 bg-slate-50/70 px-4 py-3 text-sm leading-relaxed text-slate-700">
          {item.text}
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
        <div className="mt-4">{renderItems(week.actions, "week-actions-list")}</div>
      </ConsumerPanel>
      <ConsumerPanel className="p-5" data-testid="week-risks-panel">
        <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Риски</p>
        <h2 className="mt-2 text-lg font-black text-slate-950">Что держать под контролем</h2>
        <div className="mt-4">{renderItems(week.risks, "week-risks-list")}</div>
      </ConsumerPanel>
    </div>
  );
}
