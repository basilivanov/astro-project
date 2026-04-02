import { RefreshCw } from "lucide-react";
import { MicroFeedback } from "../../../../components/MicroFeedback";
import {
  ReportRenderer,
  type ReportBlock,
} from "../../../../components/blocks/report-renderer";
import { CatalogCheckoutResumeBanner } from "../../../../components/catalog/catalog-checkout-resume";
import { EmptyState, ErrorState, LoadingState } from "../../../../components/ui-states";
import {
  ConsumerHero,
  ConsumerMetaPill,
  ConsumerPageShell,
  ConsumerPanel,
  ConsumerStatusBadge,
} from "../../../../components/consumer-page-shell";
import { ForecastSectionCard } from "../../../../components/forecast-section-card";

type ReadSection = {
  id: string;
  anchorId: string;
  title: string;
  preview: string;
  readingMinutes: number;
  blocks: ReportBlock[];
  fallbackText?: string | null;
};

type ReadPageBodyProps = {
  reportId: string;
  chartSvg?: string | null;
  shareLabel: string;
  onShare: () => void;
  sections: ReadSection[];
  expandedSections: Record<string, boolean>;
  toggleSection: (sectionId: string) => void;
  checkoutToken: string | null;
  isReady: boolean;
  initData: string;
  effectiveMode: string;
  runtimeEnabled: boolean;
};

type PendingEmptyProps = {
  showPendingState: boolean;
  showEmptyState: boolean;
};

// START_MODULE_CONTRACT: M-READ-PAGE-SECTIONS
// purpose: Render read page consumer sections separately from route orchestration.
// inputs:
//   - prepared section view models, share handler, resume token state
// outputs:
//   - stable consumer shell panels with existing test ids and copy
// invariants:
//   - section toggle, share CTA, resume banner, and feedback mount points remain unchanged
// END_MODULE_CONTRACT: M-READ-PAGE-SECTIONS

// START_MODULE_MAP: M-READ-PAGE-SECTIONS
// entrypoints:
//   - ReadLoadingShell
//   - ReadGuestShell
//   - ReadErrorShell
//   - ReadNotFoundShell
//   - ReadFailureShell
//   - ReadPageBody
// END_MODULE_MAP: M-READ-PAGE-SECTIONS

export function ReadLoadingShell() {
  return (
    <ConsumerPageShell>
      <ConsumerPanel className="p-5">
        <div data-testid="read-loading-state">
          <LoadingState compact message="Загрузка отчета..." />
        </div>
      </ConsumerPanel>
    </ConsumerPageShell>
  );
}

export function ReadGuestShell() {
  return (
    <ConsumerPageShell>
      <ConsumerHero
        eyebrow="Разбор"
        title="Нужен доступ из Telegram"
        description="Чтобы показать ваш разбор, нужно проверить права доступа и привязку к профилю."
        status={<ConsumerStatusBadge label="Закрытый доступ" description="Откройте отчет из бота" tone="slate" />}
      />
      <div className="mx-auto w-full max-w-md">
        <ConsumerPanel className="p-5">
          <EmptyState
            compact
            title="Нужен доступ из Telegram"
            message="Откройте отчет из бота, чтобы мы смогли проверить права доступа и загрузить данные."
            actionLabel="К истории отчетов"
            actionHref="/reports/history"
          />
        </ConsumerPanel>
      </div>
    </ConsumerPageShell>
  );
}

export function ReadErrorShell({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <ConsumerPageShell>
      <ConsumerHero
        eyebrow="Разбор"
        title="Разбор недоступен"
        description="Мы не смогли открыть отчет с первого раза, но экран можно безопасно перезагрузить."
        status={<ConsumerStatusBadge label="Нужен повтор" description="Данные временно недоступны" tone="rose" />}
      />
      <div className="mx-auto w-full max-w-md">
        <ConsumerPanel className="border-rose-100 p-5">
          <ErrorState compact error={error} onRetry={onRetry} />
        </ConsumerPanel>
      </div>
    </ConsumerPageShell>
  );
}

export function ReadNotFoundShell() {
  return (
    <ConsumerPageShell>
      <ConsumerHero
        eyebrow="Разбор"
        title="Отчет не найден"
        description="Этот разбор еще не готов или уже недоступен в текущем сценарии."
        status={<ConsumerStatusBadge label="Нет содержимого" description="Проверьте историю отчетов" tone="slate" />}
      />
      <div className="mx-auto w-full max-w-md">
        <ConsumerPanel className="p-5">
          <EmptyState
            compact
            title="Отчет не найден"
            message="Этот разбор еще не готов или уже недоступен."
            actionLabel="К истории отчетов"
            actionHref="/reports/history"
          />
        </ConsumerPanel>
      </div>
    </ConsumerPageShell>
  );
}

export function ReadFailureShell({
  title,
  description,
  failureSummary,
  onRetry,
  onSupport,
}: {
  title: string;
  description: string;
  failureSummary: string;
  onRetry: () => void;
  onSupport: () => void;
}) {
  return (
    <ConsumerPageShell contentClassName="gap-0 px-0 pb-24 pt-0 sm:px-0 sm:pt-0">
      <ConsumerHero
        eyebrow="Разбор"
        title={title}
        description={description}
        status={<ConsumerStatusBadge label="Нужна перегенерация" description={failureSummary} tone="amber" />}
      />
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 pb-12 pt-6 sm:px-6">
        <ConsumerPanel className="space-y-4 p-5">
          <p className="text-sm leading-relaxed text-slate-600">{failureSummary}</p>
          <div className="flex flex-wrap gap-3">
            <button type="button" onClick={onRetry} data-testid="read-failure-retry" className="rounded-full bg-slate-900 px-4 py-2.5 text-sm font-bold text-white">
              Запустить перегенерацию
            </button>
            <a href="/reports/history" onClick={onSupport} data-testid="read-failure-history" className="rounded-full border border-slate-200 px-4 py-2.5 text-sm font-bold text-slate-700">
              К истории отчетов
            </a>
          </div>
        </ConsumerPanel>
      </div>
    </ConsumerPageShell>
  );
}

function ReadPendingOrEmpty(props: PendingEmptyProps) {
  if (props.showPendingState) {
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

  if (props.showEmptyState) {
    return (
      <ConsumerPanel data-testid="report-empty-state" className="p-6">
        <EmptyState
          title="В отчете пока нет доступных блоков"
          message="Мы получили пустой или неполный ответ. Попробуйте открыть разбор позже или запустить перегенерацию."
          actionLabel="К истории отчетов"
          actionHref="/reports/history"
        />
      </ConsumerPanel>
    );
  }

  return null;
}

export function ReadPageBody(props: ReadPageBodyProps & PendingEmptyProps & {
  title: string;
  description: string;
  statusLabel: string;
  statusDescription: string;
  metaPills: Array<{ label: string; value: string }>;
  knownTimeLabel?: string | null;
  knownTimeSummary?: string | null;
  knownTimeEvidence?: string[];
}) {
  const {
    reportId,
    chartSvg,
    shareLabel,
    onShare,
    sections,
    expandedSections,
    toggleSection,
    checkoutToken,
    isReady,
    initData,
    effectiveMode,
    runtimeEnabled,
    showPendingState,
    showEmptyState,
    title,
    description,
    statusLabel,
    statusDescription,
    metaPills,
    knownTimeLabel,
    knownTimeSummary,
    knownTimeEvidence = [],
  } = props;

  return (
    <ConsumerPageShell contentClassName="gap-0 px-0 pb-24 pt-0 sm:px-0 sm:pt-0" testId="read-page">
      <ConsumerHero
        eyebrow="Разбор"
        title={title}
        description={description}
        status={<ConsumerStatusBadge label={statusLabel} description={statusDescription} tone="violet" />}
        meta={metaPills.map((pill) => <ConsumerMetaPill key={pill.label} label={pill.label} value={pill.value} />)}
      />

      <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 pb-12 pt-6 sm:px-6">
        {effectiveMode === "mock" ? null : (
          <CatalogCheckoutResumeBanner
            surface="read"
            entryPoint="read_resume_banner"
            checkoutToken={checkoutToken}
            runtimeEnabled={runtimeEnabled}
            initData={initData}
            isReady={isReady}
            mode={effectiveMode}
          />
        )}

        {((knownTimeLabel && knownTimeSummary) || knownTimeEvidence.length > 0) ? (
          <ConsumerPanel data-testid="read-known-time-panel" className="border-indigo-100 bg-indigo-50/80 p-5 shadow-sm">
            <p className="text-xs font-bold uppercase tracking-[0.24em] text-indigo-500">Контур данных</p>
            <p className="mt-2 text-base font-semibold text-slate-900">{knownTimeLabel || "Точное время сохранено"}</p>
            <p data-testid="read-known-time-summary" className="mt-1 text-sm text-slate-600">
              {(knownTimeSummary || "Контур данных подтверждён") + " • Today, Week и Read"}
            </p>
            <div data-testid="read-known-time-evidence" className="mt-3 space-y-1 text-sm font-medium text-indigo-900">
              {knownTimeEvidence.map((item) => (
                <p key={item}>{item}</p>
              ))}
            </div>
          </ConsumerPanel>
        ) : null}

        <ConsumerPanel data-testid="read-share-section" className="p-4 sm:p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Поделиться</p>
              <h2 className="mt-2 text-lg font-black tracking-tight text-slate-900">{shareLabel}</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-500">
                Внешний вид и структура чтения сохраняются. Если кнопка share недоступна, ссылка просто скопируется.
              </p>
            </div>
            <button type="button" onClick={onShare} data-testid="read-share-button" className="rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 shadow-sm transition-colors hover:bg-slate-50">
              Поделиться разбором
            </button>
          </div>
        </ConsumerPanel>

        {chartSvg && (
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
        )}

        <ReadPendingOrEmpty showPendingState={showPendingState} showEmptyState={showEmptyState} />

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
                  meta={`Секция ${String(index + 1).padStart(2, "0")} • ${section.readingMinutes} мин`}
                  expanded={Boolean(isExpanded)}
                  onToggle={() => toggleSection(section.id)}
                  badge={showsFallbackOnly ? "Текстовый режим" : null}
                >
                  <ReportRenderer blocks={section.blocks} fallbackText={section.fallbackText} fallbackTitle="Секция сохранена в упрощенном виде" />
                </ForecastSectionCard>
              </div>
            );
          })}
        </div>

        <div className="pt-4 text-center text-xs font-medium uppercase tracking-[0.28em] text-slate-400">
          <p>AstroSaaS © 2026</p>
          <p className="mt-2 opacity-60">ID: {reportId}</p>
        </div>
      </div>

    </ConsumerPageShell>
  );
}
