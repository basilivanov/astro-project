import type { NormalizedDetailFactor } from "../../lib/detail-layer";

export function DetailFactorsList({ factors, compact, testId }: { factors: NormalizedDetailFactor[]; compact?: boolean; testId?: string }) {
  if (!factors.length) return null;

  return (
    <div className="mt-4 grid gap-3" data-testid={testId}>
      {factors.map((factor) => (
        <div key={factor.id} className="rounded-2xl border border-slate-200 bg-white p-3">
          <div className="flex items-center justify-between gap-3">
            <p className={`${compact ? "text-[13px]" : "text-sm"} font-semibold text-slate-900`}>{factor.label}</p>
            {factor.value ? <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">{factor.value}</span> : null}
          </div>
          <p className={`mt-2 ${compact ? "text-[13px]" : "text-sm"} leading-relaxed text-slate-600`}>{factor.explanationHuman}</p>
          {factor.explanationAstro ? <p className="mt-2 text-xs leading-relaxed text-slate-500">{factor.explanationAstro}</p> : null}
        </div>
      ))}
    </div>
  );
}
