// ############################################################################
// AI_HEADER: MODULE_READ_REPORT_PANELS
// ROLE: Render isolated read page visual surfaces with stable semantic blocks.
// DEPENDENCIES: consumer shell, report renderer, forecast section card.
// ############################################################################

"use client";

import Link from "next/link";
import { RefreshCw } from "lucide-react";
import { ReportRenderer } from "../../../components/blocks/report-renderer";
import {
  ConsumerHero,
  ConsumerMetaPill,
  ConsumerPanel,
  ConsumerStatusBadge,
} from "../../../components/consumer-page-shell";
import { ForecastSectionCard } from "../../../components/forecast-section-card";
import { formatReadingTime, formatReportType } from "../../../lib/forecast-ui";
import type { ReadFailureContext, RenderableSection } from "./page-helpers";
import { READ_BLOCKS, READ_STATUS_META } from "./page-helpers";
import type { ReadReportControllerResult } from "./read-report-controller";

// START_MODULE_MAP: ReadReportPanels
// M-RPP-1 -> hero/header surface for completed and in-progress read states.
// M-RPP-2 -> failure/share/pending/chart panels as isolated visual units.
// M-RPP-3 -> section list rendering with stable footer and semantic block IDs.
// END_MODULE_MAP: ReadReportPanels

export function ReadHeaderPanel({ controller }: { controller: ReadReportControllerResult }) {
  const { report, title, description, clientName, readingTimeLabel, sections, statusMeta } = controller;

  return (
    <ConsumerHero
      eyebrow={formatReportType(report?.report?.report_type)}
      title={title}
      description={description}
      status={
        <ConsumerStatusBadge
          label={statusMeta.label}
          description={statusMeta.description}
          tone={statusMeta.tone}
        />
      }
      meta={
        <>
          <ConsumerMetaPill label="Для" value={clientName} />
          <ConsumerMetaPill label="Секции" value={String(sections.length)} />
          <ConsumerMetaPill label="Чтение" value={readingTimeLabel} />
          <ConsumerMetaPill label="Статус" value={statusMeta.metaValue} />
        </>
      }
    />
  );
}

export function ReadFailurePanel({
  failureContext,
  onRetry,
  onSupportClick,
}: {
  failureContext: ReadFailureContext;
  onRetry: () => void;
  onSupportClick: () => void;
}) {
  return (
    <div className="mx-auto w-full max-w-md">
      <ConsumerPanel data-testid="report-failure-surface" data-grace-surface="failure" className="p-8 text-center">
        <section data-testid="report-failure-context" data-grace-block={READ_BLOCKS.failureContext} className="space-y-4">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-rose-50 text-rose-400">
            <RefreshCw size={32} />
          </div>
          <h2 className="text-2xl font-black tracking-tight text-slate-800">Отчет не удалось собрать</h2>
          <p className="mt-3 text-sm leading-relaxed text-slate-500">
            Произошла ошибка при анализе данных. Попробуйте запустить генерацию снова, это бесплатно.
          </p>
          <p data-testid="report-failure-meta" className="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
            {failureContext.report_type} • {failureContext.entry_point}
          </p>
        </section>
        <section data-testid="report-failure-retry-block" data-grace-block={READ_BLOCKS.failureRetry} className="mt-8">
          <button
            onClick={onRetry}
            data-testid="read-regenerate-button"
            className="flex w-full items-center justify-center gap-2 rounded-[22px] bg-slate-900 py-4 font-bold text-white shadow-lg shadow-slate-200"
          >
            <RefreshCw size={20} />
            Перегенерировать
          </button>
        </section>
        <section data-testid="report-failure-support-block" data-grace-block={READ_BLOCKS.failureSupport} className="mt-6">
          <Link
            href="/reports/history"
            onClick={onSupportClick}
            data-testid="read-failure-history-link"
            className="inline-flex text-sm font-bold text-slate-500 underline underline-offset-4"
          >
            Открыть историю отчетов
          </Link>
        </section>
      </ConsumerPanel>
    </div>
  );
}


export function ReadKnownTimePanel({
  knownTimeContinuity,
}: {
  knownTimeContinuity: { label: string; value: string; evidence: string[] } | null;
}) {
  if (!knownTimeContinuity) {
    return null;
  }

  return (
    <ConsumerPanel
      data-testid="read-known-time-panel"
      className="border-indigo-100 bg-indigo-50/80 p-5 shadow-sm"
    >
      <p className="text-xs font-bold uppercase tracking-[0.24em] text-indigo-500">Контур данных</p>
      <p className="mt-2 text-base font-semibold text-slate-900">{knownTimeContinuity.label}</p>
      <p data-testid="read-known-time-summary" className="mt-1 text-sm text-slate-600">
        {knownTimeContinuity.value} • Today, Week и Read
      </p>
      <div data-testid="read-known-time-evidence" className="mt-3 space-y-1 text-sm font-medium text-indigo-900">
        {knownTimeContinuity.evidence.map((item) => (
          <p key={item}>{item}</p>
        ))}
      </div>
    </ConsumerPanel>
  );
}

export function ReadSharePanel({ onShare }: { onShare: () => void }) {
  return (
    <ConsumerPanel data-testid="read-share-section" className="p-4 sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Поделиться</p>
          <h2 className="mt-2 text-lg font-black tracking-tight text-slate-900">Отправьте ссылку на разбор без потери контекста</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-500">
            Внешний вид и структура чтения сохраняются. Если кнопка share недоступна, ссылка просто скопируется.
          </p>
        </div>
        <button
          type="button"
          onClick={onShare}
          data-testid="read-share-button"
          className="rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 shadow-sm transition-colors hover:bg-slate-50"
        >
          Поделиться разбором
        </button>
      </div>
    </ConsumerPanel>
  );
}

export function ReadChartPanel({ chartSvg }: { chartSvg: string | null }) {
  if (!chartSvg) return null;
  return (
    <ConsumerPanel className="overflow-hidden p-4 sm:p-6">
      <div className="space-y-4">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Опорная карта</p>
          <h2 className="mt-2 text-lg font-black tracking-tight text-slate-900">Визуальная схема для сверки с текстом</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-500">
            Если хотите сопоставить выводы с астрологической картой, держите схему рядом с текстовыми секциями.
          </p>
        </div>
        <div className="flex justify-center">
          <div className="chart-svg-container aspect-square w-full max-w-[500px]" dangerouslySetInnerHTML={{ __html: chartSvg }} />
        </div>
      </div>
    </ConsumerPanel>
  );
}

export function ReadPendingPanel() {
  return (
    <ConsumerPanel data-testid="read-pending-state" className="py-16 text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-slate-500">
        <RefreshCw className="animate-spin" size={32} />
      </div>
      <h3 className="mt-6 text-lg font-bold text-slate-800">Готовим отчет...</h3>
      <p className="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-slate-500">
        Анализ карты занимает 1-2 минуты. Экран можно оставить открытым.
      </p>
    </ConsumerPanel>
  );
}

export function ReadSectionsPanel({
  sections,
  expandedSections,
  onToggleSection,
  reportIdentifier,
}: {
  sections: RenderableSection[];
  expandedSections: Record<string, boolean>;
  onToggleSection: (sectionId: string) => void;
  reportIdentifier: string;
}) {
  return (
    <>
      <div className="space-y-4">
        {sections.map((section, index) => {
          const isExpanded = expandedSections[section.id];
          const showsFallbackOnly = section.blocks.length === 0 && section.fallbackText;

          return (
            <div key={section.id} data-testid={`read-section-${section.id}`}>
              <ForecastSectionCard
                index={index + 1}
                anchorId={section.anchorId}
                title={section.title}
                preview={section.preview}
                meta={`Секция ${String(index + 1).padStart(2, "0")} • ${formatReadingTime(section.readingMinutes)}`}
                expanded={Boolean(isExpanded)}
                onToggle={() => onToggleSection(section.id)}
                badge={showsFallbackOnly ? "Текстовый режим" : null}
              >
                <ReportRenderer
                  blocks={section.blocks}
                  fallbackText={section.fallbackText}
                  fallbackTitle="Секция сохранена в упрощенном виде"
                />
              </ForecastSectionCard>
            </div>
          );
        })}
      </div>
      <div className="pt-4 text-center text-xs font-medium uppercase tracking-[0.28em] text-slate-400">
        <p>AstroSaaS © 2026</p>
        <p className="mt-2 opacity-60">ID: {reportIdentifier}</p>
      </div>
    </>
  );
}
