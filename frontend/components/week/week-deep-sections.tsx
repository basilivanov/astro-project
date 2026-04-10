"use client";

import { useState } from "react";

import { ConsumerPanel } from "../consumer-page-shell";
import { ReportRenderer, extractReportFallbackText, parseReportBlocks } from "../blocks/report-renderer";
import { type WeekSurfaceModel } from "../../lib/week-brief";
import { formatSectionTitle } from "../../lib/forecast-ui";

const RAW_SLUG_PATTERN = /^[a-z0-9]+(?:[_:-][a-z0-9]+)+$/i;

function isReadableDeepText(value: string | null | undefined): value is string {
  if (typeof value !== "string") {
    return false;
  }

  const normalized = value.replace(/\s+/g, " ").trim();
  if (!normalized) {
    return false;
  }

  if (RAW_SLUG_PATTERN.test(normalized)) {
    return false;
  }

  return /\s/.test(normalized) || /[А-Яа-яA-Za-z].*[.!?,:;]/.test(normalized) || normalized.length >= 28;
}

function getSafeSectionTitle(section: WeekSurfaceModel["deepSections"][number], index: number) {
  if (isReadableDeepText(section.title)) {
    return section.title.trim();
  }

  if (isReadableDeepText(section.summary)) {
    return section.summary.trim();
  }

  return `Раздел ${index + 1}`;
}

function getSafeFallbackText(section: WeekSurfaceModel["deepSections"][number]) {
  const extracted = extractReportFallbackText(section.body_markdown);
  if (isReadableDeepText(extracted)) {
    return extracted;
  }

  if (isReadableDeepText(section.summary)) {
    return section.summary.trim();
  }

  return null;
}

export function WeekDeepSections({ week }: { week: WeekSurfaceModel }) {
  const [isOpen, setIsOpen] = useState(week.surfaceMode === "compatibility");

  if (!week.deepSections.length) {
    return (
      <ConsumerPanel className="p-5" data-testid="week-deep-sections-empty">
        <div className="space-y-2">
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Deep report layer</p>
          <h2 className="text-lg font-black text-slate-950">Развёрнутый разбор недели появится здесь</h2>
          <p className="text-sm leading-relaxed text-slate-600" data-testid="week-deep-sections-empty-copy">
            Пока показываем короткую карту недели. Полный разбор откроется, когда персональный weekly report будет готов.
          </p>
        </div>
      </ConsumerPanel>
    );
  }

  return (
    <ConsumerPanel className="p-5" data-testid="week-deep-sections">
      <div className="space-y-5">
        <div className="flex items-start justify-between gap-4">
          <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Deep report layer</p>
          <h2 className="mt-2 text-lg font-black text-slate-950">Развёрнутый разбор недели</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600" data-testid="week-deep-sections-summary">Это вторичный narrative layer: стратегия, интерпретация и markdown-блоки полного weekly report.</p>
          </div>
          <button
            type="button"
            className="inline-flex shrink-0 items-center gap-2 rounded-full border border-slate-200 px-3 py-2 text-xs font-bold text-slate-700 transition-colors hover:border-slate-300 hover:text-slate-900"
            data-testid="week-deep-sections-toggle"
            aria-expanded={isOpen}
            onClick={() => setIsOpen((value) => !value)}
          >
            {isOpen ? "Свернуть разбор" : "Открыть разбор"}
          </button>
        </div>
        <div hidden={!isOpen} aria-hidden={!isOpen} className="space-y-5">
        {week.deepSections.map((section, index) => {
          const blocks = parseReportBlocks(section.body_markdown);
          const fallbackText = getSafeFallbackText(section) ?? undefined;
          const sectionTitle = getSafeSectionTitle(section, index);
          return (
            <article key={section.id ?? index} className="space-y-3 rounded-3xl border border-slate-100 bg-white/80 p-4" data-testid={`week-deep-section-${index + 1}`}>
              <div>
                <p className="text-sm font-black text-slate-900">{sectionTitle}</p>
                {isReadableDeepText(section.summary) ? <p className="mt-1 text-xs leading-relaxed text-slate-500">{section.summary.trim()}</p> : null}
              </div>
              <ReportRenderer blocks={blocks as never} fallbackText={fallbackText} />
            </article>
          );
        })}
        </div>
      </div>
    </ConsumerPanel>
  );
}
