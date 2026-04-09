"use client";

import { cn } from "../../lib/utils";
import { type WeekSurfaceModel } from "../../lib/week-brief";

const MODE_CLASSES: Record<string, string> = {
  green: "border-emerald-100 bg-emerald-50/80 text-emerald-900",
  yellow: "border-amber-100 bg-amber-50/80 text-amber-900",
  red: "border-rose-100 bg-rose-50/80 text-rose-900",
};

export function WeekDayStrip({ week, onDayClick }: { week: WeekSurfaceModel; onDayClick: (day: string) => void }) {
  return (
    <section className="space-y-3" data-testid="week-day-strip-section">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Ритм недели</p>
          <h2 className="mt-1 text-lg font-black text-slate-950">Дни как краткий обзор</h2>
        </div>
        <p className="text-xs text-slate-500">Окно и фокус — в одной строке</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-7" data-testid="week-day-strip">
        {week.dayStrip.map((card, index) => {
          const cardKey = card.date ?? `${index}`;
          const primaryHint = card.best_for?.[0] ?? card.avoid?.[0] ?? null;
          const detailHint = card.details?.why_text ?? null;
          const detailFactors = Array.isArray(card.details?.supporting_factors) ? card.details.supporting_factors.filter((factor) => factor?.label || factor?.explanation_human) : [];
          return (
            <article
              key={cardKey}
              className={cn(
                "rounded-3xl border p-4 text-left shadow-sm",
                MODE_CLASSES[card.mode ?? "red"] ?? MODE_CLASSES.red,
              )}
              data-testid={`week-day-strip-card-${index + 1}`}
            >
              <button type="button" onClick={() => onDayClick(cardKey)} className="w-full text-left">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-black uppercase tracking-[0.12em]">{card.weekday ?? "День"}</p>
                  <p className="text-xs font-semibold">{card.score ?? 0}/100</p>
                </div>
                <p className="mt-3 text-sm font-bold leading-snug">{card.headline || "Спокойный обзор дня"}</p>
                {card.peak_window_label || primaryHint ? (
                  <p className="mt-2 text-[11px] leading-relaxed opacity-85">
                    {card.peak_window_label ? `Окно ${card.peak_window_label}` : null}
                    {card.peak_window_label && primaryHint ? " · " : null}
                    {primaryHint ? `Фокус ${primaryHint}` : null}
                  </p>
                ) : null}
                {detailHint ? <p className="mt-2 text-[11px] leading-relaxed opacity-80 line-clamp-3">{detailHint}</p> : null}
                {detailFactors.length ? (
                  <p className="mt-2 text-[11px] font-medium opacity-80">
                    {detailFactors.slice(0, 2).map((factor) => factor.label || factor.explanation_human).filter(Boolean).join(' · ')}
                  </p>
                ) : null}
              </button>
            </article>
          );
        })}
      </div>
    </section>
  );
}
