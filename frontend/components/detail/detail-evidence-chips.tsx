import type { DetailLayerImpact } from "../../lib/detail-layer";

function normalizeDisplay(value: string | null | undefined): string | null {
  const text = String(value || "").trim();
  if (!text) return null;
  const normalized = text.toLowerCase();
  if (/^[a-z]+:[a-z0-9_-]+$/i.test(text)) return null;
  if (["green", "yellow", "red", "high", "medium", "background", "low", "all_day", "morning", "evening", "week_start", "week_end"].includes(normalized)) return null;
  return text;
}

function impactLabel(impact: DetailLayerImpact): string | null {
  if (impact === "high" || impact === "medium" || impact === "low") return null;
  return null;
}

export function DetailEvidenceChips({ timeframe, impact, values = [] }: { timeframe?: string | null; impact?: DetailLayerImpact; values?: Array<string | null | undefined> }) {
  const chips = [normalizeDisplay(timeframe), impactLabel(impact), ...values.map(normalizeDisplay)].filter((item): item is string => Boolean(item));
  if (!chips.length) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-2" data-testid="detail-evidence-chips">
      {chips.map((chip, index) => (
        <span key={`${chip}-${index}`} className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-500">
          {chip}
        </span>
      ))}
    </div>
  );
}
