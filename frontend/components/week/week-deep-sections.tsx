"use client";

import { ConsumerPanel } from "../consumer-page-shell";
import { ReportRenderer, extractReportFallbackText, parseReportBlocks } from "../blocks/report-renderer";
import { type WeekSurfaceModel } from "../../lib/week-brief";

export function WeekDeepSections({ week }: { week: WeekSurfaceModel }) {
  if (!week.deepSections.length) {
    return null;
  }

  return (
    <ConsumerPanel className="p-5" data-testid="week-deep-sections">
      <div className="space-y-5">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Deep report layer</p>
          <h2 className="mt-2 text-lg font-black text-slate-950">Развёрнутый разбор недели</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-600" data-testid="week-deep-sections-summary">Здесь начинается длинный narrative layer: стратегия, интерпретация и markdown-блоки полного weekly report.</p>
        </div>
        {week.deepSections.map((section, index) => {
          const blocks = parseReportBlocks(section.body_markdown);
          const fallbackText = extractReportFallbackText(section.body_markdown) ?? section.summary ?? undefined;
          return (
            <article key={section.id ?? index} className="space-y-3 rounded-3xl border border-slate-100 bg-white/80 p-4" data-testid={`week-deep-section-${index + 1}`}>
              <div>
                <p className="text-sm font-black text-slate-900">{section.title}</p>
                {section.summary ? <p className="mt-1 text-xs leading-relaxed text-slate-500">{section.summary}</p> : null}
              </div>
              <ReportRenderer blocks={blocks as never} fallbackText={fallbackText} />
            </article>
          );
        })}
      </div>
    </ConsumerPanel>
  );
}
