"use client";

import { ConsumerPanel } from "../consumer-page-shell";
import { DetailEvidenceChips } from "../detail/detail-evidence-chips";
import { type WeekSurfaceModel } from "../../lib/week-brief";

type WeekDayDrawerCard = WeekSurfaceModel["dayCards"][number];

function resolveDrawerCopy(card: WeekDayDrawerCard, surfaceMode: WeekSurfaceModel["surfaceMode"]) {
  const detailLine = String(card.details?.why_text || card.lead || "").trim() || null;
  if (detailLine) return detailLine;
  if (surfaceMode === "compatibility") {
    return "Совместимый обзор дня без глубокой детализации: держите только лучший ход и главный риск.";
  }
  return "Этот день держится в общем ритме недели: используйте его как короткий drill-down, а не как отдельный дневной отчёт.";
}

export function WeekDayDrawer({
  card,
  surfaceMode,
}: {
  card: WeekDayDrawerCard | null;
  surfaceMode: WeekSurfaceModel["surfaceMode"];
}) {
  if (!card) return null;

  const headline = String(card.headline || "").trim() || "День без отдельного акцента";
  const bestFor = (card.best_for ?? []).filter(Boolean).slice(0, 2);
  const avoid = (card.avoid ?? []).filter(Boolean).slice(0, 2);
  const isCompatibility = surfaceMode === "compatibility";
  const detailLine = resolveDrawerCopy(card, surfaceMode);
  const scoreLabel = typeof card.score === "number" ? `${card.score}/100` : null;

  return (
    <ConsumerPanel className="p-5" data-testid="week-day-drawer">
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Деталь дня</p>
            <h2 className="mt-2 text-lg font-black text-slate-950">{card.weekday ?? "День недели"}</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">{headline}</p>
          </div>
          {scoreLabel ? <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-black text-slate-700">{scoreLabel}</span> : null}
        </div>

        <DetailEvidenceChips timeframe={card.peak_window_label} values={[isCompatibility ? "Лёгкий fallback-обзор" : "Короткий drill-down дня"]} />

        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-2xl border border-emerald-100 bg-emerald-50/70 p-4" data-testid="week-day-drawer-best-for">
            <p className="text-[11px] font-black uppercase tracking-[0.18em] text-emerald-700">Лучше для</p>
            <p className="mt-2 text-sm leading-relaxed text-slate-700">{bestFor.length ? bestFor.join(" · ") : "Держите ритм простым и не дробите внимание."}</p>
          </div>
          <div className="rounded-2xl border border-rose-100 bg-rose-50/70 p-4" data-testid="week-day-drawer-avoid">
            <p className="text-[11px] font-black uppercase tracking-[0.18em] text-rose-700">Избегать</p>
            <p className="mt-2 text-sm leading-relaxed text-slate-700">{avoid.length ? avoid.join(" · ") : "Не превращайте день в отдельный большой прогноз."}</p>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4" data-testid="week-day-drawer-detail">
          <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-400">Почему день так звучит</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-700">{detailLine}</p>
        </div>
      </div>
    </ConsumerPanel>
  );
}
