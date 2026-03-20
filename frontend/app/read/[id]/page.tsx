// ############################################################################
// AI_HEADER: MODULE_READ_PAGE
// ROLE: Display generated report to user.
// DEPENDENCIES: useTelegram, api/reports/{id}.
// ############################################################################

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { ArrowLeft, Clock3, ListChecks, RefreshCw } from "lucide-react";
import { useTelegram } from "../../../hooks/useTelegram";
import {
  ReportRenderer,
  parseReportBlocks,
  extractReportFallbackText,
  hasReportContent,
  type ReportBlock,
} from "../../../components/blocks/report-renderer";
import { MicroFeedback } from "../../../components/MicroFeedback";
import { trackEvent } from "../../lib/analytics";
import { EmptyState, ErrorState, LoadingState } from "../../../components/ui-states";
import {
  ConsumerHero,
  ConsumerMetaPill,
  ConsumerPageShell,
  ConsumerPanel,
  ConsumerStatusBadge,
} from "../../../components/consumer-page-shell";
import { ForecastSectionCard } from "../../../components/forecast-section-card";
import {
  buildSectionAnchorId,
  estimateReadingMinutes,
  extractSectionPreview,
  formatReadingTime,
  formatReportType,
  formatSectionTitle,
} from "../../../lib/forecast-ui";

type ReportChunk = {
  id?: string;
  section?: string;
  title?: string | null;
  content?: unknown;
};

type ReportPayload = {
  report?: {
    id?: string;
    report_type?: string;
    status?: string;
    client_name?: string;
    access_source?: string | null;
  };
  chunks?: ReportChunk[];
  chart_svg?: string | null;
};

type RenderableSection = {
  id: string;
  anchorId: string;
  section: string;
  title: string;
  blocks: ReportBlock[];
  fallbackText: string | null;
  preview: string | null;
  readingMinutes: number;
};

const SECTION_FALLBACK_MESSAGE =
  "Исходный формат секции не удалось разобрать полностью. Показываем безопасную текстовую версию, чтобы содержание не потерялось.";
export default function ReadReportPage() {
  const params = useParams<{ id?: string | string[] }>();
  const searchParams = useSearchParams();
  const reportId =
    typeof params?.id === "string" ? params.id : Array.isArray(params?.id) ? params.id[0] : "";
  const { user, initData, isReady, mode } = useTelegram();
  const isGuestRoute = searchParams.get("guest") === "1";
  const isMockRoute = searchParams.get("mock") === "1";
  const effectiveMode = isGuestRoute ? "guest" : isMockRoute ? "mock" : mode;
  const effectiveInitData = initData;
  const [report, setReport] = useState<ReportPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const startTime = useRef<number>(Date.now());

  const loadReport = async () => {
    if (!effectiveInitData || !reportId) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`/api/reports/${reportId}`, {
        headers: {
          "X-Telegram-Auth": effectiveInitData,
        },
      });

      if (!res.ok) {
        let message = res.status === 404 ? "Отчет не найден" : "Не удалось загрузить отчет";
        try {
          const payload = await res.json();
          if (payload?.detail && typeof payload.detail === "string") {
            message = payload.detail;
          }
        } catch {
          // Keep the fallback message when the response is not JSON.
        }
        throw new Error(message);
      }

      const data = (await res.json()) as ReportPayload;
      const sections = prepareRenderableSections(data?.chunks);

      setReport(data);
      setExpandedSections(buildExpandedSections(sections));

      if (user?.id) {
        trackEvent("report_opened", {
          telegramId: user.id,
          metadata: {
            report_id: reportId,
            type: data?.report?.report_type || "unknown",
          },
        });
      }
    } catch (loadError) {
      setReport(null);
      setExpandedSections({});
      setError(toErrorMessage(loadError, "Не удалось загрузить отчет"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if ((isReady || isMockRoute) && effectiveInitData && reportId) {
      loadReport();
    }
  }, [isReady, isMockRoute, effectiveInitData, reportId]);

  useEffect(() => {
    startTime.current = Date.now();

    return () => {
      const elapsed = Date.now() - startTime.current;
      if (elapsed > 1000) {
        trackEvent("time_on_report", {
          metadata: { report_id: reportId, duration_ms: elapsed },
        });
      }
    };
  }, [reportId]);

  const sections = useMemo(() => prepareRenderableSections(report?.chunks), [report?.chunks]);
  const reportStatus = report?.report?.status || "pending";
  const statusMeta = READ_STATUS_META[reportStatus] || READ_STATUS_META.pending;
  const title = formatReportType(report?.report?.report_type || "report");
  const clientName = report?.report?.client_name || "Клиент";
  const chartSvg = typeof report?.chart_svg === "string" ? report.chart_svg : null;
  const accessSource = report?.report?.access_source || null;
  const showPendingState = sections.length === 0 && reportStatus !== "completed";
  const showEmptyState = sections.length === 0 && reportStatus === "completed";
  const openedCount = sections.filter((section) => expandedSections[section.id]).length;
  const totalReadingMinutes = sections.reduce((sum, section) => sum + section.readingMinutes, 0);
  const allSectionsExpanded =
    sections.length > 0 && sections.every((section) => expandedSections[section.id]);

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => ({ ...prev, [sectionId]: !prev[sectionId] }));
  };

  const toggleAllSections = () => {
    const nextExpandedValue = !allSectionsExpanded;
    setExpandedSections(
      sections.reduce<Record<string, boolean>>((acc, section) => {
        acc[section.id] = nextExpandedValue;
        return acc;
      }, {}),
    );
  };

  const handleRegenerate = async () => {
    if (!effectiveInitData || !reportId) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/reports/${reportId}/regenerate`, {
        method: "POST",
        headers: {
          "X-Telegram-Auth": effectiveInitData,
        },
      });
      if (!res.ok) throw new Error("Не удалось запустить перегенерацию");
      window.location.reload();
    } catch (regenerateError) {
      setError(toErrorMessage(regenerateError, "Не удалось запустить перегенерацию"));
      setLoading(false);
    }
  };

  if ((!isReady && !isMockRoute) || loading) {
    return (
      <ConsumerPageShell>
        <ConsumerPanel className="p-5">
          <LoadingState compact message="Загрузка отчета..." />
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
          status={
            <ConsumerStatusBadge
              label="Закрытый доступ"
              description="Откройте отчет из бота"
              tone="slate"
            />
          }
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
          status={
            <ConsumerStatusBadge label="Нужен повтор" description="Данные временно недоступны" tone="rose" />
          }
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
          status={
            <ConsumerStatusBadge label="Нет содержимого" description="Проверьте историю отчетов" tone="slate" />
          }
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
      <ConsumerPageShell>
        <ConsumerHero
          eyebrow="Разбор"
          title={title}
          description="Сборка не завершилась, но сценарий можно перезапустить без потери контекста."
          status={
            <ConsumerStatusBadge
              label="Не удалось собрать"
              description="Попробуйте перегенерацию"
              tone="rose"
            />
          }
          meta={<ConsumerMetaPill label="Для" value={clientName} />}
        />
        <div className="mx-auto w-full max-w-md">
          <ConsumerPanel className="p-8 text-center">
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-rose-50 text-rose-400">
              <RefreshCw size={32} />
            </div>
            <h2 className="text-2xl font-black tracking-tight text-slate-800">Отчет не удалось собрать</h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-500">
              Произошла ошибка при анализе данных. Попробуйте запустить генерацию снова, это бесплатно.
            </p>
            <button
              onClick={handleRegenerate}
              className="mt-8 flex w-full items-center justify-center gap-2 rounded-[22px] bg-slate-900 py-4 font-bold text-white shadow-lg shadow-slate-200"
            >
              <RefreshCw size={20} />
              Перегенерировать
            </button>
          <Link
            href="/reports/history"
            className="mt-6 inline-flex text-sm font-bold text-slate-400 transition-colors hover:text-slate-600"
          >
            Вернуться в историю
          </Link>
          </ConsumerPanel>
        </div>
      </ConsumerPageShell>
    );
  }

  return (
    <ConsumerPageShell contentClassName="gap-0 px-0 pb-24 pt-0 sm:px-0 sm:pt-0">
      <div data-testid="read-sticky-panel" className="sticky top-0 z-20 border-b border-white/70 bg-white/78 px-4 py-3 shadow-sm shadow-slate-100/70 backdrop-blur-xl sm:px-6">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-3">
          <Link
            href="/reports/history"
            aria-label="К истории отчетов"
            className="flex h-10 w-10 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
          >
            <ArrowLeft size={22} strokeWidth={1.8} />
          </Link>
          <div className="min-w-0 text-center">
            <p className="text-[10px] font-black uppercase tracking-[0.22em] text-slate-400">Разбор</p>
            <h1 className="truncate text-sm font-black text-slate-800">{title}</h1>
          </div>
          <div className="w-10" />
        </div>
      </div>

      <div className="px-4 py-6 sm:px-6 sm:py-8">
        <div className="mx-auto max-w-3xl space-y-5">
          <ConsumerHero
            eyebrow="Разбор"
            title={title}
            description={buildReadDescription(reportStatus, clientName, sections.length)}
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
                {accessSource && (
                  <ConsumerMetaPill label="Доступ" value={formatAccessSource(accessSource)} />
                )}
                <ConsumerMetaPill
                  label="Секций"
                  value={reportStatus === "completed" ? String(sections.length) : statusMeta.metaValue}
                />
                <ConsumerMetaPill
                  label="Чтение"
                  value={reportStatus === "completed" ? `~${formatReadingTime(totalReadingMinutes)}` : "После генерации"}
                />
              </>
            }
            actions={
              reportStatus === "completed" && sections.length > 1 ? (
                <button
                  onClick={toggleAllSections}
                  className="rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 shadow-sm transition-colors hover:bg-slate-50"
                >
                  {allSectionsExpanded ? "Свернуть все" : "Раскрыть все"}
                </button>
              ) : null
            }
          />

          {sections.length > 0 && (
            <ConsumerPanel data-testid="read-overview-panel" className="p-4 sm:p-5">
              <div className="flex items-start gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 shadow-sm">
                  <ListChecks size={20} />
                </div>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Навигация по разбору</p>
                    <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.16em] text-slate-500">
                      Открыто {openedCount} из {sections.length}
                    </span>
                  </div>
                  <h2 className="mt-2 text-lg font-black tracking-tight text-slate-900">
                    Сначала выберите нужный блок, а не читайте весь отчет подряд
                  </h2>
                  <p className="mt-2 text-sm leading-relaxed text-slate-500">
                    Превью и оценка времени помогают быстро войти в тему. Начните с секции, которая ближе к вашей задаче, и возвращайтесь к остальным по мере необходимости.
                  </p>
                </div>
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <article className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                  <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Шаг 1</p>
                  <p className="mt-2 text-sm font-black text-slate-900">Сверьтесь с превью</p>
                  <p className="mt-2 text-sm leading-relaxed text-slate-500">
                    Короткое описание секции показывает, о чём блок и зачем в него заходить.
                  </p>
                </article>
                <article className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                  <div className="flex items-center gap-2">
                    <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Шаг 2</p>
                    <Clock3 size={14} className="text-slate-400" />
                  </div>
                  <p className="mt-2 text-sm font-black text-slate-900">Ориентируйтесь по времени</p>
                  <p className="mt-2 text-sm leading-relaxed text-slate-500">
                    У каждой секции есть оценка чтения, чтобы проще выбрать быстрый проход или полный разбор.
                  </p>
                </article>
                <article className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                  <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Шаг 3</p>
                  <p className="mt-2 text-sm font-black text-slate-900">Раскрывайте все только при сравнении</p>
                  <p className="mt-2 text-sm leading-relaxed text-slate-500">
                    Кнопка выше нужна для сквозного чтения. В обычном сценарии точечное раскрытие воспринимается легче.
                  </p>
                </article>
              </div>

              <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
                {sections.map((section, index) => (
                  <a
                    key={section.id}
                    href={`#${section.anchorId}`}
                    className="min-w-[220px] rounded-[22px] border border-slate-200 bg-white px-4 py-3 shadow-sm transition-colors hover:border-indigo-200 hover:bg-indigo-50/40"
                  >
                    <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
                      Секция {String(index + 1).padStart(2, "0")} • {formatReadingTime(section.readingMinutes)}
                    </p>
                    <p className="mt-2 text-sm font-black leading-snug text-slate-900">{section.title}</p>
                    <p className="mt-2 text-sm leading-relaxed text-slate-500">
                      {section.preview || "Откройте секцию, чтобы посмотреть содержание целиком."}
                    </p>
                  </a>
                ))}
              </div>
            </ConsumerPanel>
          )}

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
                  <div
                    className="chart-svg-container aspect-square w-full max-w-[500px]"
                    dangerouslySetInnerHTML={{ __html: chartSvg }}
                  />
                </div>
              </div>
            </ConsumerPanel>
          )}

          {showPendingState && (
            <ConsumerPanel className="py-16 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-slate-500">
                <RefreshCw className="animate-spin" size={32} />
              </div>
              <h3 className="mt-6 text-lg font-bold text-slate-800">Готовим отчет...</h3>
              <p className="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-slate-500">
                Анализ карты занимает 1-2 минуты. Экран можно оставить открытым.
              </p>
            </ConsumerPanel>
          )}

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

          <div className="space-y-4">
            {sections.map((section, index) => {
              const isExpanded = expandedSections[section.id];
              const showsFallbackOnly = section.blocks.length === 0 && section.fallbackText;

              return (
                <ForecastSectionCard
                  key={section.id}
                  index={index + 1}
                  anchorId={section.anchorId}
                  title={section.title}
                  preview={section.preview}
                  meta={`Секция ${String(index + 1).padStart(2, "0")} • ${formatReadingTime(section.readingMinutes)}`}
                  expanded={Boolean(isExpanded)}
                  onToggle={() => toggleSection(section.id)}
                  badge={showsFallbackOnly ? "Текстовый режим" : null}
                >
                  <ReportRenderer
                    blocks={section.blocks}
                    fallbackText={section.fallbackText}
                    fallbackTitle="Секция сохранена в упрощенном виде"
                  />
                </ForecastSectionCard>
              );
            })}
          </div>

          <div className="pt-4 text-center text-xs font-medium uppercase tracking-[0.28em] text-slate-400">
            <p>AstroSaaS © 2026</p>
            <p className="mt-2 opacity-60">ID: {report.report.id || reportId}</p>
          </div>
        </div>
      </div>

      <MicroFeedback reportId={reportId} />
    </ConsumerPageShell>
  );
}

const buildExpandedSections = (sections: RenderableSection[]) =>
  sections.slice(0, 2).reduce<Record<string, boolean>>((acc, section) => {
    acc[section.id] = true;
    return acc;
  }, {});

const prepareRenderableSections = (chunks: unknown): RenderableSection[] => {
  if (!Array.isArray(chunks)) {
    return [];
  }

  return chunks.flatMap((chunk, index) => {
    const section =
      typeof chunk?.section === "string" && chunk.section.trim().length > 0
        ? chunk.section
        : `section_${index + 1}`;
    const blocks = parseReportBlocks(chunk?.content);
    const fallbackText =
      blocks.length === 0
        ? extractReportFallbackText(chunk?.content) ??
          (hasReportContent(chunk?.content) ? SECTION_FALLBACK_MESSAGE : null)
        : null;

    if (blocks.length === 0 && !fallbackText) {
      return [];
    }

    return [
      {
        id:
          typeof chunk?.id === "string" && chunk.id.trim().length > 0
            ? chunk.id
            : section,
        anchorId: buildSectionAnchorId(
          typeof chunk?.id === "string" && chunk.id.trim().length > 0 ? chunk.id : section,
          "read",
        ),
        section,
        title:
          typeof chunk?.title === "string" && chunk.title.trim().length > 0
            ? chunk.title.trim()
            : formatSectionTitle(section),
        blocks,
        fallbackText,
        preview: extractSectionPreview({ blocks, fallbackText }),
        readingMinutes: estimateReadingMinutes({ blocks, fallbackText }),
      },
    ];
  });
};

const buildReadDescription = (status: string, clientName: string, sectionCount: number) => {
  if (status === "completed") {
    return `Разбор уже собран для ${clientName} и разбит на ${sectionCount} секций. Сначала просмотрите превью, затем раскрывайте только те части, где нужен более детальный ориентир.`;
  }

  if (status === "in_progress" || status === "pending") {
    return `Отчет для ${clientName} еще в работе. Как только секции будут готовы, экран останется в том же сценарии и покажет структуру чтения.`;
  }

  if (sectionCount === 0) {
    return `Разбор для ${clientName} пока не содержит доступных блоков. Можно вернуться позже или запустить повторную сборку.`;
  }

  return `Разбор для ${clientName} доступен в секциях: сначала главная канва, затем детальные блоки по темам.`;
};

const formatAccessSource = (accessSource: string) => {
  if (accessSource === "report_entitlement") {
    return "Разовый unlock";
  }
  if (accessSource === "subscription") {
    return "Подписка";
  }
  if (accessSource === "credits") {
    return "Пакет вопросов";
  }
  if (accessSource === "trial") {
    return "Пробный доступ";
  }
  if (accessSource === "bypass") {
    return "Внутренний доступ";
  }
  return accessSource;
};

const READ_STATUS_META: Record<
  string,
  { label: string; description: string; tone: "emerald" | "indigo" | "amber" | "rose" | "slate"; metaValue: string }
> = {
  completed: {
    label: "Готов к чтению",
    description: "Структура уже собрана по секциям",
    tone: "emerald",
    metaValue: "Готово",
  },
  in_progress: {
    label: "В обработке",
    description: "Секции еще собираются",
    tone: "indigo",
    metaValue: "В работе",
  },
  pending: {
    label: "Ожидает сборку",
    description: "Сценарий еще не завершен",
    tone: "amber",
    metaValue: "Ожидание",
  },
  failed: {
    label: "Ошибка сборки",
    description: "Нужен повторный запуск",
    tone: "rose",
    metaValue: "Сбой",
  },
};

const toErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return fallback;
};
