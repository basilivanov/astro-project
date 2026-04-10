"use client";

// START_MODULE_CONTRACT: M-WEEK-DAY-GRID
// INTENT: Render week day cards as first-class detail cards with compact overview plus disclosure details.
// INPUTS: Normalized week surface model and interaction callback.
// OUTPUTS: Detail-aware weekly day card grid.
// INVARIANTS: Ordering mirrors `week.dayCards`; overview remains stable; disclosure uses shared detail primitives.
// END_MODULE_CONTRACT: M-WEEK-DAY-GRID

import { useState } from "react";

import { DetailDisclosureCard } from "../detail/detail-disclosure-card";
import { DetailEvidenceChips } from "../detail/detail-evidence-chips";
import { type NormalizedDetailFactor } from "../../lib/detail-layer";
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

function mapDayFactors(card: WeekSurfaceModel["dayCards"][number], index: number): NormalizedDetailFactor[] {
  return (card.supporting_factors ?? [])
    .map((factor, factorIndex) => {
      const label = String(factor?.label || "").trim();
      const explanationHuman = String(factor?.explanation_human || "").trim();
      const explanationAstro = String(factor?.explanation_astro || "").trim();
      const value = String(factor?.value || "").trim();
      if (!label && !explanationHuman && !explanationAstro) return null;
      return {
        id: `week-day-${index + 1}-factor-${factorIndex + 1}`,
        label: label || `Фактор ${factorIndex + 1}`,
        explanationHuman: explanationHuman || explanationAstro,
        explanationAstro: explanationAstro || null,
        value: value || null,
        impact: null,
        source: "week_supporting_factor" as const,
        relatedKey: card.date ?? `week-day-${index + 1}`,
      };
    })
    .filter((item): item is NormalizedDetailFactor => Boolean(item));
}

function buildDayDetailBody(card: WeekSurfaceModel["dayCards"][number]): string | null {
  const parts = [card.lead, card.headline]
    .map((value) => String(value || "").trim())
    .filter(Boolean);
  if (!parts.length) return null;
  return Array.from(new Set(parts)).join(" ");
}

function buildDayDetailSummary(card: WeekSurfaceModel["dayCards"][number]): string | null {
  if (card.practical?.length) {
    return `Лучше: ${card.practical.join(" · ")}`;
  }
  if (card.avoid?.length) {
    return `Избегать: ${card.avoid.join(" · ")}`;
  }
  return null;
}

export function WeekDayGrid({ week, onDayClick }: { week: WeekSurfaceModel; onDayClick: (day: string) => void }) {
  const [openKey, setOpenKey] = useState<string | null>(null);
  const isCompatibilityGrid = week.surfaceMode === "compatibility";
  const seenCompatibilityHeadlines = new Set<string>();

  return (
    <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-7" data-testid="week-day-grid">
      {week.dayCards.map((card, index) => {
        const cardKey = card.date ?? `${index}`;
        const normalizedHeadline = String(card.headline ?? "").trim().toLowerCase();
        const compatibilityHeadline = isCompatibilityGrid && normalizedHeadline
          ? (seenCompatibilityHeadlines.has(normalizedHeadline) ? "День держит тот же ритм" : card.headline)
          : card.headline;
        if (isCompatibilityGrid && normalizedHeadline) {
          seenCompatibilityHeadlines.add(normalizedHeadline);
        }
        const compatibilityPrimaryHint = card.best_for?.[0] ?? card.avoid?.[0] ?? null;
        return (
          <article
            key={cardKey}
            className={cn(
              "rounded-3xl border p-4 text-left shadow-sm",
              MODE_CLASSES[card.mode ?? "red"] ?? MODE_CLASSES.red,
            )}
            data-testid={`week-day-card-${index + 1}`}
          >
            <button type="button" onClick={() => onDayClick(cardKey)} className="w-full text-left">
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-black uppercase tracking-[0.18em]">{DAY_LABELS[card.weekday ?? ""] ?? card.weekday ?? "День"}</p>
                {typeof card.score === "number" ? <p className="text-xs font-semibold">{card.score}/100</p> : null}
              </div>
              <p className="mt-3 text-sm font-bold leading-snug">{compatibilityHeadline || "Краткий обзор дня"}</p>
              {isCompatibilityGrid ? null : card.lead ? <p className="mt-2 text-xs leading-relaxed opacity-85">{card.lead}</p> : null}
            </button>
            <DetailEvidenceChips timeframe={card.peak_window_label} values={[isCompatibilityGrid ? compatibilityPrimaryHint : card.practical?.[0] ?? null]} />
            {card.practical?.length && !isCompatibilityGrid ? <p className="mt-3 text-xs">Лучше: {card.practical.join(" · ")}</p> : null}
            {card.avoid?.length ? <p className="mt-1 text-xs">Избегать: {card.avoid.join(" · ")}</p> : null}
            {isCompatibilityGrid ? (
              <p className="mt-3 text-[11px] font-medium text-slate-500">Совместимый fallback-обзор без глубокой детализации.</p>
            ) : (
              <DetailDisclosureCard
                testId={`week-day-detail-${index + 1}`}
                title="Детали дня"
                summary={buildDayDetailSummary(card)}
                body={buildDayDetailBody(card)}
                factors={mapDayFactors(card, index)}
                compact
                isOpen={openKey === cardKey}
                onToggle={() => setOpenKey((current) => (current === cardKey ? null : cardKey))}
              />
            )}
          </article>
        );
      })}
    </section>
  );
}
