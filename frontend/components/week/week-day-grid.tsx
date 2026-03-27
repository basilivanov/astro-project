"use client";

import { cn } from "../../lib/utils";
import { type WeekSurfaceModel } from "../../lib/week-brief";

const DAY_LABELS: Record<string, string> = {
  mon: "Пн",
  tue: "Вт",
  wed: "Ср",
  thu: "Чт",
  fri: "Пт",
  sat: "Сб",
  sun: "Вс",
};

const MODE_CLASSES: Record<string, string> = {
  green: "border-emerald-100 bg-emerald-50/80 text-emerald-900",
  yellow: "border-amber-100 bg-amber-50/80 text-amber-900",
  red: "border-rose-100 bg-rose-50/80 text-rose-900",
};

export function WeekDayGrid({ week, onDayClick }: { week: WeekSurfaceModel; onDayClick: (day: string) => void }) {
  return (
    <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-7" data-testid="week-day-grid">
      {week.dayCards.map((card, index) => (
        <button
          key={`${card.date ?? index}`}
          type="button"
          onClick={() => onDayClick(card.date ?? `${index}`)}
          className={cn(
            "rounded-3xl border p-4 text-left shadow-sm transition-transform hover:-translate-y-0.5",
            MODE_CLASSES[card.mode ?? "red"] ?? MODE_CLASSES.red,
          )}
          data-testid={`week-day-card-${index + 1}`}
        >
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-black uppercase tracking-[0.18em]">{DAY_LABELS[card.weekday ?? ""] ?? card.weekday ?? "День"}</p>
            <p className="text-xs font-semibold">{card.score ?? 0}/100</p>
          </div>
          <p className="mt-3 text-sm font-bold leading-snug">{card.headline}</p>
          {card.peak_window_label ? <p className="mt-2 text-xs opacity-80">Пик: {card.peak_window_label}</p> : null}
          {card.best_for?.length ? <p className="mt-3 text-xs">Лучше: {card.best_for.join(" · ")}</p> : null}
          {card.avoid?.length ? <p className="mt-1 text-xs">Избегать: {card.avoid.join(" · ")}</p> : null}
        </button>
      ))}
    </section>
  );
}
