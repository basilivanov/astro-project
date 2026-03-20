"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowRight, Calendar, Clock3, ListChecks, Loader2, Sparkles } from "lucide-react";
import { useTelegram } from "../../hooks/useTelegram";
import { EmptyState, ErrorState, LoadingState } from "../../components/ui-states";
import {
  ReportRenderer,
  parseReportBlocks,
  extractReportFallbackText,
  hasReportContent,
  type ReportBlock,
} from "../../components/blocks/report-renderer";
import {
  ConsumerHero,
  ConsumerMetaPill,
  ConsumerPageShell,
  ConsumerPanel,
  ConsumerStatusBadge,
} from "../../components/consumer-page-shell";
import { ForecastSectionCard } from "../../components/forecast-section-card";
import {
  buildSectionAnchorId,
  estimateReadingMinutes,
  extractSectionPreview,
  formatReadingTime,
  formatSectionTitle,
} from "../../lib/forecast-ui";

const SECTION_FALLBACK_MESSAGE =
  "Исходный формат секции не удалось разобрать полностью. Показываем безопасную текстовую версию, чтобы содержание не потерялось.";

type WeekReportSummary = {
  id?: string;
  report_type?: string;
  status?: string;
};

type WeekReportChunk = {
  id?: string;
  section?: string;
  title?: string | null;
  content?: unknown;
};

type WeekReportPayload = {
  report?: WeekReportSummary;
  chunks?: WeekReportChunk[];
};

type WeekSection = {
  id: string;
  anchorId: string;
  title: string;
  blocks: ReportBlock[];
  fallbackText: string | null;
  preview: string | null;
  readingMinutes: number;
};

type MockWeekWindow = Window & {
  MOCK_WEEK_REPORT_OVERRIDE?: unknown;
};

function WeekPageContent() {
  const { initData, isReady, mode } = useTelegram();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const isMockRoute = searchParams.get("mock") === "1";
  const [latestReport, setLatestReport] = useState<WeekReportPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  const sections = useMemo(() => prepareWeekSections(latestReport?.chunks), [latestReport?.chunks]);
  const report = latestReport?.report;
  const status = report?.status || "empty";
  const expandedCount = sections.filter((section) => expandedSections[section.id]).length;
  const totalReadingMinutes = sections.reduce((sum, section) => sum + section.readingMinutes, 0);
  const statusMeta = WEEK_STATUS_META[status] || WEEK_STATUS_META.empty;

  const fetchLatest = async () => {
    if (!initData) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`/api/reports/my?limit=5&t=${Date.now()}`, {
        headers: { "X-Telegram-Auth": initData },
      });

      if (!res.ok) {
        throw new Error("Не удалось получить список прогнозов");
      }

      const data = await res.json();
      const weekSummary = Array.isArray(data)
        ? data.find((item: WeekReportSummary) => item.report_type === "week_forecast")
        : null;

      if (!weekSummary) {
        setLatestReport(null);
        setExpandedSections({});
        return;
      }

      if (weekSummary.status !== "completed") {
        setLatestReport({ report: weekSummary, chunks: [] });
        setExpandedSections({});
        return;
      }

      const fullRes = await fetch(`/api/reports/${weekSummary.id}`, {
        headers: { "X-Telegram-Auth": initData },
      });

      if (!fullRes.ok) {
        throw new Error("Не удалось загрузить полный недельный прогноз");
      }

      const fullData = (await fullRes.json()) as WeekReportPayload;
      const nextSections = prepareWeekSections(fullData.chunks);

      setLatestReport(fullData);
      setExpandedSections((prev) =>
        Object.keys(prev).length > 0 ? prev : buildWeekExpandedSections(nextSections),
      );
    } catch (fetchError) {
      console.error("Fetch latest fail", fetchError);
      setLatestReport(null);
      setExpandedSections({});
      setError(toErrorMessage(fetchError, "Не удалось обновить недельный прогноз"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isReady && mode === "mock" && isMockRoute) {
      const mockWindow = window as MockWeekWindow;
      const mockReport = normalizeMockWeekPayload(mockWindow.MOCK_WEEK_REPORT_OVERRIDE);
      const mockSections = prepareWeekSections(mockReport?.chunks);

      setLatestReport(mockReport);
      setExpandedSections(buildWeekExpandedSections(mockSections));
      setLoading(false);
      setError(null);
      return;
    }

    if (isReady && initData) {
      fetchLatest();
    }

    if (isReady && !initData) {
      setLoading(false);
    }

    const handleVisibility = () => {
      if (!document.hidden && initData) {
        fetchLatest();
      }
    };

    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, [isReady, initData, isMockRoute, mode, pathname]);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | undefined;

    if (status === "in_progress") {
      timer = setInterval(() => {
        fetchLatest();
      }, 3000);
    }

    return () => {
      if (timer) {
        clearInterval(timer);
      }
    };
  }, [status]);

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => ({ ...prev, [sectionId]: !prev[sectionId] }));
  };

  if (!isReady || loading) {
    return (
      <ConsumerPageShell testId="week-page">
        <ConsumerPanel className="p-5">
          <LoadingState compact message="Собираем недельный навигатор..." />
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  if (mode === "guest" || mode === "none" || !initData) {
    return (
      <ConsumerPageShell testId="week-page">
        <ConsumerHero
          eyebrow="Неделя"
          title="Навигатор недели"
          description="Прогноз собирается в связке с Telegram-профилем, чтобы учесть доступ и привязанные данные."
          status={
            <ConsumerStatusBadge
              label="Нужен вход"
              description="Откройте экран из бота"
              tone="slate"
            />
          }
        />
        <ConsumerPanel className="p-5">
          <EmptyState
            compact
            title="Неделя пока недоступна"
            message="Откройте этот экран из Telegram-бота, чтобы мы смогли проверить доступ и показать ваш прогноз."
            actionLabel="К истории отчетов"
            actionHref="/reports/history"
          />
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  if (error) {
    return (
      <ConsumerPageShell testId="week-page">
        <ConsumerHero
          eyebrow="Неделя"
          title="Навигатор недели"
          description="Мы не смогли обновить сводку с первого раза, но сам сценарий экрана сохраняется."
          status={
            <ConsumerStatusBadge label="Нужен повтор" description="Сервис временно не ответил" tone="rose" />
          }
        />
        <ConsumerPanel className="border-rose-100 p-5">
          <ErrorState compact error={error} onRetry={fetchLatest} />
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  return (
    <ConsumerPageShell testId="week-page">
      <ConsumerHero
        eyebrow="Неделя"
        title="Навигатор недели"
        description={buildWeekDescription(status, sections.length)}
        status={
          <ConsumerStatusBadge
            label={statusMeta.label}
            description={statusMeta.description}
            tone={statusMeta.tone}
          />
        }
        meta={
          <>
            <ConsumerMetaPill
              label="Секций"
              value={status === "completed" ? String(sections.length) : statusMeta.metaValue}
            />
            <ConsumerMetaPill
              label="Чтение"
              value={status === "completed" ? `~${formatReadingTime(totalReadingMinutes)}` : "После генерации"}
            />
            <ConsumerMetaPill
              label="Открыто"
              value={status === "completed" ? `${expandedCount} из ${sections.length}` : "После генерации"}
            />
          </>
        }
        actions={
          status === "completed" && report?.id ? (
            <Link
              href={`/read/${report.id}`}
              className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-slate-200"
            >
              Открыть разбор
              <ArrowRight size={16} />
            </Link>
          ) : null
        }
      />

      {status === "completed" ? (
        <>
          <ConsumerPanel data-testid="week-overview-panel" className="p-4 sm:p-5">
            <div className="flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 shadow-sm">
                <ListChecks size={20} />
              </div>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Маршрут чтения</p>
                  <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.16em] text-slate-500">
                    Открыто {expandedCount} из {sections.length}
                  </span>
                </div>
                <h2 className="mt-2 text-lg font-black tracking-tight text-slate-900">
                  Сначала канва недели, затем только нужные секции
                </h2>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">
                  Превью помогает быстро понять, где у недели главный фокус. Читайте не подряд, а по задаче: выберите нужный блок и откройте его без перегруза.
                </p>
              </div>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <article className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Шаг 1</p>
                <p className="mt-2 text-sm font-black text-slate-900">Просмотрите превью</p>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">
                  За 1-2 минуты видно, где неделя поддерживает рост, а где просит аккуратности.
                </p>
              </article>
              <article className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                <div className="flex items-center gap-2">
                  <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Шаг 2</p>
                  <Clock3 size={14} className="text-slate-400" />
                </div>
                <p className="mt-2 text-sm font-black text-slate-900">Оцените время</p>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">
                  Каждая секция помечена по длительности, чтобы легко выбрать короткий или полный проход.
                </p>
              </article>
              <article className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Шаг 3</p>
                <p className="mt-2 text-sm font-black text-slate-900">Уходите в полный разбор</p>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">
                  Если нужен весь сценарий целиком, откройте полный экран чтения из кнопки выше.
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

          <div className="space-y-4">
            {sections.map((section, index) => (
              <ForecastSectionCard
                key={section.id}
                index={index + 1}
                anchorId={section.anchorId}
                title={section.title}
                preview={section.preview}
                meta={`Секция ${String(index + 1).padStart(2, "0")} • ${formatReadingTime(section.readingMinutes)}`}
                expanded={Boolean(expandedSections[section.id])}
                onToggle={() => toggleSection(section.id)}
                badge={section.blocks.length === 0 && section.fallbackText ? "Текстовый режим" : null}
              >
                <ReportRenderer
                  blocks={section.blocks}
                  fallbackText={section.fallbackText}
                  fallbackTitle="Секция сохранена в упрощенном виде"
                />
              </ForecastSectionCard>
            ))}
          </div>
        </>
      ) : (
        <ConsumerPanel className="overflow-hidden p-7">
          <div className="relative z-10 space-y-5">
            <div className="flex h-14 w-14 items-center justify-center rounded-[24px] bg-indigo-50 text-indigo-600 shadow-sm">
              <Calendar size={30} strokeWidth={1.5} />
            </div>

            <div>
              <h2 className="text-2xl font-black leading-tight text-slate-950">Подробный план на 7 дней</h2>
              <p className="mt-3 text-sm leading-relaxed text-slate-500">
                Узнайте главную тему недели, ритм, зоны риска и лучшие моменты для действий без лишней воды.
              </p>
            </div>

            {status === "in_progress" ? (
              <div className="flex items-center justify-center gap-2 rounded-[22px] border border-indigo-100 bg-indigo-50 py-4 font-bold text-indigo-700">
                <Loader2 className="animate-spin" size={18} />
                Готовим прогноз...
              </div>
            ) : status === "failed" ? (
              <Link
                href="/create?type=week_forecast"
                className="flex items-center justify-center gap-2 rounded-[22px] border border-rose-100 bg-rose-50 py-4 font-bold text-rose-700"
              >
                <Sparkles size={18} />
                Перегенерировать
                <ArrowRight size={18} />
              </Link>
            ) : (
              <Link
                href="/create?type=week_forecast"
                className="flex items-center justify-center gap-2 rounded-[22px] bg-slate-900 py-4 font-bold text-white shadow-lg shadow-slate-200"
              >
                <Sparkles size={18} />
                Получить прогноз
                <ArrowRight size={18} />
              </Link>
            )}
          </div>
        </ConsumerPanel>
      )}
    </ConsumerPageShell>
  );
}

export default function WeekPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <WeekPageContent />
    </Suspense>
  );
}

const buildWeekExpandedSections = (sections: WeekSection[]) =>
  sections.slice(0, 2).reduce<Record<string, boolean>>((acc, section) => {
    acc[section.id] = true;
    return acc;
  }, {});

const prepareWeekSections = (chunks: unknown): WeekSection[] => {
  if (!Array.isArray(chunks)) {
    return [];
  }

  return chunks.flatMap((chunk, index) => {
    const sectionId =
      typeof chunk?.id === "string" && chunk.id.trim().length > 0
        ? chunk.id
        : typeof chunk?.section === "string" && chunk.section.trim().length > 0
          ? chunk.section
          : `week_section_${index + 1}`;

    const sectionKey =
      typeof chunk?.section === "string" && chunk.section.trim().length > 0
        ? chunk.section
        : `week_section_${index + 1}`;

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
        id: sectionId,
        anchorId: buildSectionAnchorId(sectionId, "week"),
        title:
          typeof chunk?.title === "string" && chunk.title.trim().length > 0
            ? chunk.title.trim()
            : formatSectionTitle(sectionKey),
        blocks,
        fallbackText,
        preview: extractSectionPreview({ blocks, fallbackText }),
        readingMinutes: estimateReadingMinutes({ blocks, fallbackText }),
      },
    ];
  });
};

const normalizeMockWeekPayload = (value: unknown): WeekReportPayload | null => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }

  return value as WeekReportPayload;
};

const buildWeekDescription = (status: string, sectionCount: number) => {
  if (status === "completed") {
    return `Сценарий недели уже собран по ${sectionCount} секциям. Сначала считайте общую канву, затем раскрывайте детали только там, где нужен более точный ориентир.`;
  }

  if (status === "in_progress") {
    return "Прогноз уже собирается. Экран останется в сценарии продукта и обновится, как только секции будут готовы.";
  }

  if (status === "failed") {
    return "Последняя сборка не завершилась, но недельный сценарий можно перезапустить без лишних шагов.";
  }

  return "Здесь появляется структурированный план на 7 дней: главная тема, рабочий ритм, риски и точки усиления.";
};

const WEEK_STATUS_META: Record<
  string,
  { label: string; description: string; tone: "emerald" | "indigo" | "amber" | "rose" | "slate"; metaValue: string }
> = {
  completed: {
    label: "Неделя готова",
    description: "Можно читать и возвращаться к секциям",
    tone: "emerald",
    metaValue: "Готово",
  },
  in_progress: {
    label: "Собираем прогноз",
    description: "Обычно это занимает 1-2 минуты",
    tone: "indigo",
    metaValue: "В работе",
  },
  failed: {
    label: "Нужен повтор",
    description: "Последняя генерация завершилась с ошибкой",
    tone: "rose",
    metaValue: "Сбой",
  },
  empty: {
    label: "Пока пусто",
    description: "Прогноз еще не создан",
    tone: "slate",
    metaValue: "Нет данных",
  },
};

const toErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return fallback;
};
