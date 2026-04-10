"use client";

import { ConsumerPanel } from "../consumer-page-shell";
import { DetailEvidenceChips } from "../detail/detail-evidence-chips";

type WeekDayDrawerCard = {
  id?: string | null;
  date?: string | null;
  weekday?: string | null;
  headline?: string | null;
  score?: number | null;
  mode?: string | null;
  lead?: string | null;
  best_for?: string[] | null;
  avoid?: string[] | null;
  peak_window_label?: string | null;
  details?: {
    why_text?: string | null;
  } | null;
};
type WeekDayDrawerProps = {
  card: WeekDayDrawerCard | null;
  surfaceMode: "canonical" | "compatibility";
};

function buildGenericDrawerLine(card: WeekDayDrawerCard, surfaceMode: WeekDayDrawerProps["surfaceMode"]) {
  const best = (card.best_for ?? []).filter(Boolean)[0] ?? null;
  const avoid = (card.avoid ?? []).filter(Boolean)[0] ?? null;
  const headline = String(card.headline || "").trim() || null;

  if (surfaceMode === "compatibility") {
    if (best && avoid) {
      return `День лучше отдавать под ${best.toLowerCase()}, а от ${avoid.toLowerCase()} лучше держать дистанцию.`;
    }
    if (best) {
      return `День лучше проживается через ${best.toLowerCase()} без лишнего расширения планов.`;
    }
    if (avoid) {
      return `Лучше держать день простым и не уходить в ${avoid.toLowerCase()}.`;
    }
    if (headline) {
      return `${headline} Держите день коротким и не перегружайте его лишними ожиданиями.`;
    }
    return "Смотрите на этот день как на короткий ориентир: один лучший ход и один риск под контролем.";
  }

  if (best && avoid) {
    return `Лучше всего день раскрывается через ${best.toLowerCase()}, если не уводить его в ${avoid.toLowerCase()}.`;
  }
  if (best) {
    return `Главная польза дня раскрывается через ${best.toLowerCase()} и спокойную точную подачу.`;
  }
  if (avoid) {
    return `День лучше звучит, если не уводить его в ${avoid.toLowerCase()} и не перегружать темп.`;
  }
  if (headline) {
    return `${headline} Смотрите на день как на короткое уточнение к общей картине недели.`;
  }
  return "Этот день лучше читать как короткое уточнение к общей картине недели, а не как отдельный большой прогноз.";
}

function resolveDrawerCopy(card: WeekDayDrawerCard, surfaceMode: WeekDayDrawerProps["surfaceMode"]) {
  const detailLine = String(card.details?.why_text || card.lead || "").trim() || null;
  if (detailLine) return detailLine;
  return buildGenericDrawerLine(card, surfaceMode);
}

export function WeekDayDrawer({ card, surfaceMode }: WeekDayDrawerProps) {
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

        <DetailEvidenceChips timeframe={card.peak_window_label} values={[isCompatibility ? "Короткий обзор дня" : "Деталь к общей картине"]} />

        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-2xl border border-emerald-100 bg-emerald-50/70 p-4" data-testid="week-day-drawer-best-for">
            <p className="text-[11px] font-black uppercase tracking-[0.18em] text-emerald-700">Лучше для</p>
            <p className="mt-2 text-sm leading-relaxed text-slate-700">{bestFor.length ? bestFor.join(" · ") : "Держите ритм простым и не дробите внимание."}</p>
          </div>
          <div className="rounded-2xl border border-rose-100 bg-rose-50/70 p-4" data-testid="week-day-drawer-avoid">
            <p className="text-[11px] font-black uppercase tracking-[0.18em] text-rose-700">Избегать</p>
            <p className="mt-2 text-sm leading-relaxed text-slate-700">{avoid.length ? avoid.join(" · ") : "Не перегружайте день лишними ожиданиями."}</p>
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
