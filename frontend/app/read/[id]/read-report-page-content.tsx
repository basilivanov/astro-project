// ############################################################################
// AI_HEADER: MODULE_READ_REPORT_PAGE_CONTENT
// ROLE: Orchestrate read report controller state and compose read surfaces.
// DEPENDENCIES: read-report-controller, read-report-panels, read-report-actions.
// ############################################################################

"use client";

import { CatalogCheckoutResumeBanner } from "../../../components/catalog/catalog-checkout-resume";
import { ConsumerHero, ConsumerMetaPill, ConsumerPageShell, ConsumerPanel, ConsumerStatusBadge } from "../../../components/consumer-page-shell";
import { MicroFeedback } from "../../../components/MicroFeedback";
import { EmptyState, ErrorState, LoadingState } from "../../../components/ui-states";
import { buildResumeActionHandler, buildRetryAction, buildShareAction, buildSupportAction } from "./read-report-actions";
import { useReadReportController } from "./read-report-controller";
import { ReadChartPanel, ReadFailurePanel, ReadHeaderPanel, ReadKnownTimePanel, ReadPendingPanel, ReadSectionsPanel, ReadSharePanel } from "./read-report-panels";
import { READ_DIRECT_ENTRY_POINT, READ_ENTRY_POINT } from "./page-helpers";

// START_MODULE_MAP: ReadReportPageContent
// M-RPC-1 -> route params/search params normalization and read controller state.
// M-RPC-2 -> share/resume/failure actions with telemetry-preserving wrappers.
// M-RPC-3 -> guarded fallback surfaces for loading/access/error/empty states.
// M-RPC-4 -> success composition for header/share/chart/pending/sections/footer feedback.
// END_MODULE_MAP: ReadReportPageContent

export function ReadReportPageContent() {
  const controller = useReadReportController();
  const {
    chartSvg,
    checkoutToken,
    clientName,
    effectiveInitData,
    effectiveMode,
    error,
    expandedSections,
    fetchFailureContext,
    handleRetrySuccess,
    handleTrackCatalogEvent,
    isMockRoute,
    isReady,
    loadReport,
    loading,
    knownTimeContinuity,
    report,
    reportId,
    runtimeEnabled,
    sections,
    setError,
    showEmptyState,
    showPendingState,
    title,
    toggleSection,
    trackReadEvent,
    correlate,
  } = controller;

  const handleShare = buildShareAction({
    reportId,
    shareUrl: controller.shareUrl,
    setError,
    trackReadEvent,
  });

  const handleResumeCTA = buildResumeActionHandler({
    reportId,
    reportType: report?.report?.report_type,
    trackReadEvent,
  });

  const handleRetry = buildRetryAction({
    effectiveInitData,
    reportId,
    fetchFailureContext,
    onTrackCatalogEvent: handleTrackCatalogEvent,
    correlate,
    onSuccess: handleRetrySuccess,
    onError: setError,
  });

  const handleSupportCTA = buildSupportAction({
    fetchFailureContext,
    onTrackCatalogEvent: handleTrackCatalogEvent,
    correlate,
  });

  if ((!isReady && !isMockRoute) || loading) {
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

  if (effectiveMode === "guest" || effectiveMode === "none" || !effectiveInitData) {
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

  if (error) {
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
            <ErrorState compact error={error} onRetry={loadReport} />
          </ConsumerPanel>
        </div>
      </ConsumerPageShell>
    );
  }

  if (!report?.report) {
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

  if (report.report.status === "failed") {
    return (
      <ConsumerPageShell contentClassName="gap-0 px-0 pb-24 pt-0 sm:px-0 sm:pt-0">
        {checkoutToken && (
          <div data-testid="read-resume-entry" className="px-4 pt-6 sm:px-6 sm:pt-8">
            <div className="mx-auto max-w-3xl">
              <CatalogCheckoutResumeBanner
                surface="read"
                entryPoint={READ_ENTRY_POINT}
                checkoutToken={checkoutToken}
                mockEnabled={isMockRoute}
                runtimeEnabled={runtimeEnabled}
                initData={effectiveInitData}
                isReady={isReady || isMockRoute}
                mode={effectiveMode}
                onTrackAction={handleResumeCTA}
              />
            </div>
          </div>
        )}
        <ConsumerHero
          eyebrow="Разбор"
          title={title}
          description="Сборка не завершилась, но сценарий можно перезапустить без потери контекста."
          status={<ConsumerStatusBadge label="Не удалось собрать" description="Попробуйте перегенерацию" tone="rose" />}
          meta={<ConsumerMetaPill label="Для" value={clientName} />}
        />
        <ReadFailurePanel failureContext={fetchFailureContext()} onRetry={handleRetry} onSupportClick={handleSupportCTA} />
      </ConsumerPageShell>
    );
  }

  return (
    <ConsumerPageShell testId="read-page" contentClassName="gap-0 px-0 pb-24 pt-0 sm:px-0 sm:pt-0">
      {checkoutToken && (
        <div data-testid="read-resume-entry" className="px-4 pt-6 sm:px-6 sm:pt-8">
          <div className="mx-auto max-w-3xl">
            <CatalogCheckoutResumeBanner
              surface="read"
              entryPoint={checkoutToken ? READ_ENTRY_POINT : READ_DIRECT_ENTRY_POINT}
              checkoutToken={checkoutToken}
              mockEnabled={isMockRoute}
              runtimeEnabled={runtimeEnabled}
              initData={effectiveInitData}
              isReady={isReady || isMockRoute}
              mode={effectiveMode}
              onTrackAction={handleResumeCTA}
            />
          </div>
        </div>
      )}
      <ReadHeaderPanel controller={controller} />
      <div className="px-4 sm:px-6">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
          <ReadKnownTimePanel knownTimeContinuity={knownTimeContinuity} />
          <ReadSharePanel onShare={handleShare} />
          <ReadChartPanel chartSvg={chartSvg} />
          {showPendingState && <ReadPendingPanel />}
          {showEmptyState && (
            <ConsumerPanel data-testid="report-empty-state" className="p-6">
              <EmptyState
                title="В отчете пока нет доступных блоков"
                message="Мы получили пустой или неполный ответ. Попробуйте открыть разбор позже или запустить перегенерацию."
                actionLabel="К истории отчетов"
                actionHref="/reports/history"
              />
            </ConsumerPanel>
          )}
          <ReadSectionsPanel
            sections={sections}
            expandedSections={expandedSections}
            onToggleSection={toggleSection}
            reportIdentifier={report.report.id || reportId}
          />
        </div>
      </div>
      <MicroFeedback reportId={reportId} />
    </ConsumerPageShell>
  );
}
