"use client";

// START_MODULE_CONTRACT: M-WEEK-DAY-GRID
// INTENT: Render clickable daily cards for the week detail surface.
// INPUTS: `week` surface model with day cards and a day selection callback.
// OUTPUTS: Grid of semantic day buttons with mode styling and compact evidence.
// INVARIANTS: Cards remain pure view projections; click payload resolves to card date or stable index fallback.
// SIDE_EFFECTS: Delegates interaction through `onDayClick` only.
// DEPENDENCIES: Utility class merger and week brief surface model.
// FAILURE_MODES: Unknown mode falls back to red styling; missing date keys degrade to index-based stable fallback.
// CALLERS: `frontend/app/week/page.tsx` week detail composition.
// NOTES: Annotation wave adds structural coordinates without visual/behavioral churn.
// END_MODULE_CONTRACT: M-WEEK-DAY-GRID

// START_MODULE_MAP: M-WEEK-DAY-GRID
// EXPORTS: WeekDayGrid.
// INTERNALS: DAY_LABELS, MODE_CLASSES.
// DATA_FLOW: day cards -> mode/date label resolution -> button projection -> day callback dispatch.
// UI_SEAMS: `week-day-grid`, `week-day-card-*`.
// END_MODULE_MAP: M-WEEK-DAY-GRID

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

// START_FUNCTION_CONTRACT: WeekDayGrid
// INTENT: Project normalized week day cards into an interactive overview grid.
// INPUTS: Week surface model and click handler.
// OUTPUTS: Section with day buttons.
// INVARIANTS: Button ordering mirrors `week.dayCards`; mode styling and labels are derived without mutation.
// END_FUNCTION_CONTRACT: WeekDayGrid
export function WeekDayGrid({ week, onDayClick }: { week: WeekSurfaceModel; onDayClick: (day: string) => void }) {
  return (
    // START_BLOCK: WEEK_DAY_CARD_GRID
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
          {/* START_BLOCK: WEEK_DAY_CARD_CONTENT */}
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-black uppercase tracking-[0.18em]">{DAY_LABELS[card.weekday ?? ""] ?? card.weekday ?? "День"}</p>
            <p className="text-xs font-semibold">{card.score ?? 0}/100</p>
          </div>
          <p className="mt-3 text-sm font-bold leading-snug">{card.headline}</p>
          {card.peak_window_label ? <p className="mt-2 text-xs opacity-80">Пик: {card.peak_window_label}</p> : null}
          {card.best_for?.length ? <p className="mt-3 text-xs">Лучше: {card.best_for.join(" · ")}</p> : null}
          {card.avoid?.length ? <p className="mt-1 text-xs">Избегать: {card.avoid.join(" · ")}</p> : null}
          {/* END_BLOCK: WEEK_DAY_CARD_CONTENT */}
        </button>
      ))}
    </section>
    // END_BLOCK: WEEK_DAY_CARD_GRID
  );
}
