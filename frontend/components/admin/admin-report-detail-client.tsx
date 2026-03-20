"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Download, FileText, RefreshCw, AlertTriangle, CheckCircle2, Clock3, Loader2 } from "lucide-react";

import ReportSectionAccordion from "../report-section-accordion";

type AdminReport = {
  id: string;
  report_type: string;
  status: string;
  paid: boolean;
  error_message?: string | null;
  error_at?: string | null;
  created_at: string;
  updated_at: string;
  client_id: string;
  client_name: string;
  chunk_count: number;
};

type AdminReportChunk = {
  id: string;
  section: string;
  title?: string | null;
  status: string;
  error_message?: string | null;
  error_at?: string | null;
  order_index: number;
  content?: string | null;
  content_html?: string | null;
  created_at: string;
};

type AdminReportRun = {
  id: string;
  status: string;
  error_message?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  estimated_cost?: number;
  created_at: string;
};

type AdminReportDetail = {
  report: AdminReport;
  chunks: AdminReportChunk[];
  runs: AdminReportRun[];
  chart_svg?: string | null;
};

type Props = {
  initialData: AdminReportDetail;
  errorMessage?: string | null;
};

type QueueItem = {
  id: string;
  label: string;
  status: string;
  updatedAt?: string | null;
};

const DEFAULT_SECTION_ORDER = [
  "executive_summary",
  "core_identity",
  "personal_potential",
  "shadow_patterns",
  "love_intimacy",
  "money_realization",
  "social_destiny",
  "family_roots",
  "career_calling",
  "spiritual_vector",
  "health_energy",
  "timing_cycles",
  "crisis_growth",
  "integration_path",
  "final_synthesis",
];

const CALL_OUT_SECTIONS = new Set(["executive_summary", "final_synthesis"]);
const FALLBACK_MARKERS = [
  "дополнено автоматически",
  "fallback",
  "автоматически",
  "repair",
  "validator",
];

const formatDateTime = (value?: string | null) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium", timeStyle: "short" }).format(date);
};

const formatReportType = (value: string) => value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());

const badgeTone = (status: string) => {
  switch (status) {
    case "completed":
    case "done":
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    case "in_progress":
    case "running":
      return "bg-amber-50 text-amber-700 border-amber-200";
    case "failed":
    case "error":
      return "bg-rose-50 text-rose-700 border-rose-200";
    default:
      return "bg-slate-50 text-slate-600 border-slate-200";
  }
};

const prettyStatus = (status: string) => {
  switch (status) {
    case "completed": return "done";
    case "in_progress": return "running";
    case "failed": return "error";
    default: return status || "pending";
  }
};

const statusIcon = (status: string) => {
  switch (status) {
    case "completed":
    case "done":
      return <CheckCircle2 className="h-4 w-4" />;
    case "in_progress":
    case "running":
      return <Loader2 className="h-4 w-4 animate-spin" />;
    case "failed":
    case "error":
      return <AlertTriangle className="h-4 w-4" />;
    default:
      return <Clock3 className="h-4 w-4" />;
  }
};

const buildProgress = (report: AdminReport, chunks: AdminReportChunk[]) => {
  const total = chunks.length;
  const completed = chunks.filter((chunk) => chunk.status === "completed").length;
  const runningChunk = chunks.find((chunk) => chunk.status === "in_progress");
  const failedChunk = chunks.find((chunk) => chunk.status === "failed");
  const percent = report.status === "completed" ? 100 : total > 0 ? Math.round((completed / total) * 100) : 0;

  let label = "Ждём запуск";
  let detail = "Очередь ещё не тронула секции.";
  if (failedChunk || report.status === "failed") {
    label = "Есть ошибка";
    detail = `Проверьте секцию ${failedChunk?.title || failedChunk?.section || "отчёта"}.`;
  } else if (runningChunk) {
    label = `Сейчас идёт ${runningChunk.title || runningChunk.section}`;
    detail = `Готово ${completed} из ${total}.`;
  } else if (report.status === "completed") {
    label = "Отчёт собран";
    detail = `Все секции доступны. Готово ${completed} из ${total}.`;
  } else if (completed > 0) {
    label = "Движение есть";
    detail = `Уже готовы ${completed} из ${total}.`;
  }

  return { total, completed, percent, label, detail };
};

const parseBlocks = (content?: string | null) => {
  if (!content) return [] as Array<Record<string, unknown>>;
  try {
    const parsed = JSON.parse(content);
    if (Array.isArray(parsed)) return parsed;
    if (parsed && typeof parsed === "object") return [parsed as Record<string, unknown>];
  } catch {}
  return [] as Array<Record<string, unknown>>;
};

const extractPreview = (content?: string | null) => {
  if (!content) return "";
  const blocks = parseBlocks(content);
  const blockText = blocks
    .flatMap((block) => {
      if (typeof block?.text === "string") return [block.text];
      if (typeof block?.content === "string") return [block.content];
      if (typeof block?.body === "string") return [block.body];
      if (Array.isArray(block?.items)) return block.items.filter((item): item is string => typeof item === "string");
      return [];
    })
    .join(" ")
    .trim();
  const raw = blockText || content;
  return raw.replace(/```[\s\S]*?```/g, " ").replace(/\s+/g, " ").trim().slice(0, 240);
};

const hasFallbackMarker = (content?: string | null, errorMessage?: string | null) => {
  const haystack = `${content || ""} ${errorMessage || ""}`.toLowerCase();
  return FALLBACK_MARKERS.some((marker) => haystack.includes(marker));
};

const buildMarkdown = (chunks: AdminReportChunk[]) => {
  return chunks
    .slice()
    .sort((left, right) => left.order_index - right.order_index)
    .map((chunk) => {
      const heading = `## ${chunk.title || chunk.section}`;
      if (!chunk.content) return `${heading}\n\n_Секция пока без контента._`;
      const blocks = parseBlocks(chunk.content);
      if (!blocks.length) return `${heading}\n\n${chunk.content}`;
      const body = blocks
        .map((block) => {
          if (typeof block.text === "string") return block.text;
          if (typeof block.content === "string") return block.content;
          if (typeof block.body === "string") return block.body;
          if (Array.isArray(block.items)) return block.items.map((item) => `- ${String(item)}`).join("\n");
          if (typeof block.title === "string") return `### ${block.title}`;
          return "";
        })
        .filter(Boolean)
        .join("\n\n");
      return `${heading}\n\n${body || "_Секция сохранена в структурированном виде._"}`;
    })
    .join("\n\n");
};

const downloadBlob = (filename: string, mime: string, content: string | Blob) => {
  const blob = content instanceof Blob ? content : new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

export default function AdminReportDetailClient({ initialData, errorMessage }: Props) {
  const [data, setData] = useState(initialData);
  const [refreshTick, setRefreshTick] = useState(0);
  const [busyAll, setBusyAll] = useState(false);
  const [toast, setToast] = useState<{ kind: "error" | "success"; text: string } | null>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [queueValue, setQueueValue] = useState("");

  const report = data.report;
  const sortedChunks = useMemo(() => {
    const rank = new Map(DEFAULT_SECTION_ORDER.map((id, index) => [id, index]));
    return [...data.chunks].sort((left, right) => {
      const leftRank = rank.get(left.section) ?? left.order_index + 100;
      const rightRank = rank.get(right.section) ?? right.order_index + 100;
      return leftRank - rightRank;
    });
  }, [data.chunks]);

  const progress = useMemo(() => buildProgress(report, sortedChunks), [report, sortedChunks]);
  const markdown = useMemo(() => buildMarkdown(sortedChunks), [sortedChunks]);

  const refreshData = useCallback(async () => {
    const response = await fetch(`/api/admin/reports/${report.id}?include_content=1`, { cache: "no-store" });
    if (!response.ok) throw new Error(`refresh_failed_${response.status}`);
    const payload = (await response.json()) as AdminReportDetail;
    setData(payload);
    return payload;
  }, [report.id]);

  useEffect(() => {
    if (!["in_progress", "pending"].includes(report.status)) return;
    const timer = window.setInterval(() => {
      void refreshData().catch(() => undefined);
    }, 5000);
    return () => window.clearInterval(timer);
  }, [refreshData, report.status]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 4000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const launchAll = useCallback(async () => {
    setBusyAll(true);
    try {
      const response = await fetch(`/api/admin/reports/${report.id}/regenerate/async`, { method: "POST" });
      if (!response.ok) throw new Error(`regen_all_${response.status}`);
      await refreshData();
      setRefreshTick((value) => value + 1);
      setToast({ kind: "success", text: "Запуск принят. Идём по секциям последовательно." });
    } catch {
      setToast({ kind: "error", text: "Не удалось запустить полную генерацию." });
    } finally {
      setBusyAll(false);
    }
  }, [refreshData, report.id]);

  const enqueueReport = useCallback(async () => {
    const reportId = queueValue.trim();
    if (!reportId) return;
    try {
      const response = await fetch(`/api/admin/reports/${reportId}`);
      if (!response.ok) throw new Error(`queue_${response.status}`);
      const payload = (await response.json()) as AdminReportDetail;
      setQueue((items) => {
        if (items.some((item) => item.id === reportId)) return items;
        return [
          ...items,
          { id: payload.report.id, label: payload.report.client_name || payload.report.id, status: payload.report.status, updatedAt: payload.report.updated_at },
        ];
      });
      setQueueValue("");
      setToast({ kind: "success", text: "Отчёт добавлен в очередь наблюдения." });
    } catch {
      setToast({ kind: "error", text: "Не удалось добавить отчёт в очередь." });
    }
  }, [queueValue]);

  useEffect(() => {
    if (!queue.length) return;
    const timer = window.setInterval(async () => {
      const updated = await Promise.all(
        queue.map(async (item) => {
          try {
            const response = await fetch(`/api/admin/reports/${item.id}`);
            if (!response.ok) return item;
            const payload = (await response.json()) as AdminReportDetail;
            return { ...item, status: payload.report.status, updatedAt: payload.report.updated_at };
          } catch {
            return item;
          }
        })
      );
      setQueue(updated);
    }, 7000);
    return () => window.clearInterval(timer);
  }, [queue]);

  const markdownFilename = `${report.client_name || report.id}-natal-master.md`.replace(/\s+/g, "-").toLowerCase();
  const pdfFilename = `${report.client_name || report.id}-natal-master.pdf`.replace(/\s+/g, "-").toLowerCase();

  const downloadMarkdown = () => downloadBlob(markdownFilename, "text/markdown;charset=utf-8", markdown);
  const downloadPdf = () => downloadBlob(pdfFilename, "application/pdf", markdown);

  return (
    <div className="flex flex-col gap-6 py-6 pb-24">
      {toast ? (
        <div className={`fixed right-4 top-4 z-50 rounded-2xl border px-4 py-3 text-sm shadow-lg ${toast.kind === "error" ? "border-rose-200 bg-rose-50 text-rose-700" : "border-emerald-200 bg-emerald-50 text-emerald-700"}`}>
          {toast.text}
        </div>
      ) : null}

      <header className="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-slate-400">Админ · natal_master</p>
            <h1 className="mt-2 text-2xl font-black text-slate-900 sm:text-3xl">{report.client_name || "Отчёт без имени"}</h1>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">{formatReportType(report.report_type)} · создан {formatDateTime(report.created_at)} · обновлён {formatDateTime(report.updated_at)}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-wide ${badgeTone(report.status)}`}>{statusIcon(report.status)} {prettyStatus(report.status)}</span>
            {report.paid ? <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-bold uppercase tracking-wide text-emerald-700">оплачен</span> : null}
          </div>
        </div>
        {errorMessage ? <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{errorMessage}</div> : null}
        {report.error_message ? <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">Ошибка пайплайна: {report.error_message}</div> : null}
      </header>

      <div className="sticky top-0 z-30 -mx-4 border-y border-slate-200 bg-slate-50/95 px-4 py-3 backdrop-blur md:mx-0 md:rounded-2xl md:border md:px-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-3 text-sm text-slate-600">
              <span className="font-semibold text-slate-900">{progress.label}</span>
              <span>{progress.completed}/{progress.total} секций · {progress.percent}%</span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200">
              <div className="h-full rounded-full bg-purple-600 transition-all" style={{ width: `${progress.percent}%` }} />
            </div>
            <p className="mt-2 text-xs text-slate-500">{progress.detail}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => void refreshData()} className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm">
              <RefreshCw className="h-4 w-4" /> Обновить
            </button>
            <button type="button" onClick={() => void launchAll()} disabled={busyAll} className="inline-flex items-center gap-2 rounded-2xl bg-purple-600 px-4 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-60">
              {busyAll ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />} Сгенерить всё
            </button>
            <button type="button" onClick={downloadMarkdown} className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm">
              <FileText className="h-4 w-4" /> Скачать Markdown
            </button>
            <button type="button" onClick={downloadPdf} className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm">
              <Download className="h-4 w-4" /> Скачать PDF
            </button>
          </div>
        </div>
      </div>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-6">
          {data.chart_svg ? (
            <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
              <h2 className="text-lg font-bold text-slate-900">Карта рождения</h2>
              <div className="chart-svg-container mt-4 w-full overflow-hidden" dangerouslySetInnerHTML={{ __html: data.chart_svg }} />
            </div>
          ) : null}

          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold text-slate-900">Секции отчёта</h2>
                <p className="text-sm text-slate-500">Первые три аккордеона открыты сразу, чтобы редактор быстро проверил старт текста.</p>
              </div>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">{sortedChunks.length}</span>
            </div>
            <div className="space-y-4">
              {sortedChunks.map((chunk, index) => {
                const preview = extractPreview(chunk.content);
                const fallback = hasFallbackMarker(chunk.content, chunk.error_message);
                const quickNote = CALL_OUT_SECTIONS.has(chunk.section) ? (
                  <div className={`mb-3 rounded-2xl border px-4 py-3 text-sm ${fallback ? "border-amber-200 bg-amber-50 text-amber-800" : "border-sky-200 bg-sky-50 text-sky-800"}`}>
                    <div className="font-semibold">{chunk.section === "executive_summary" ? "Быстрый взгляд на opening" : "Быстрый взгляд на closing"}</div>
                    <div className="mt-1 leading-relaxed">{preview || "Секция ещё не заполнилась."}</div>
                    {fallback ? <div className="mt-2 text-xs font-semibold uppercase tracking-wide">Внимание: видны fallback-маркеры</div> : null}
                  </div>
                ) : null;

                return (
                  <div key={`${chunk.id}-${refreshTick}`}>
                    {quickNote}
                    <ReportSectionAccordion
                      reportId={report.id}
                      chunk={chunk}
                      meta={`#${index + 1} · ${formatDateTime(chunk.created_at)} · ${chunk.section}`}
                      badgeClassName={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${badgeTone(chunk.status)}`}
                      errorAtLabel={formatDateTime(chunk.error_at)}
                      initiallyOpen={index < 3}
                    />
                  </div>
                );
              })}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
            <h2 className="text-lg font-bold text-slate-900">Журнал событий</h2>
            <div className="mt-4 space-y-3">
              {data.runs.length === 0 ? (
                <p className="text-sm text-slate-500">Запусков пока нет.</p>
              ) : (
                data.runs.map((run, index) => (
                  <div key={run.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="text-sm font-semibold text-slate-900">Запуск #{data.runs.length - index}</div>
                      <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${badgeTone(run.status)}`}>{statusIcon(run.status)} {prettyStatus(run.status)}</span>
                    </div>
                    <div className="mt-2 text-xs leading-relaxed text-slate-500">Создан {formatDateTime(run.created_at)} · старт {formatDateTime(run.started_at)} · финиш {formatDateTime(run.finished_at)} · токены {run.total_tokens || 0}</div>
                    {run.error_message ? <div className="mt-2 text-sm text-rose-700">{run.error_message}</div> : null}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <aside className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
            <h2 className="text-lg font-bold text-slate-900">Очередь отчётов</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">Можно наблюдать несколько отчётов сразу: вставьте `id` и держите руку на пульсе.</p>
            <div className="mt-4 flex gap-2">
              <input value={queueValue} onChange={(event) => setQueueValue(event.target.value)} placeholder="ID отчёта" className="min-w-0 flex-1 rounded-2xl border border-slate-200 px-3 py-2 text-sm outline-none ring-0 placeholder:text-slate-400" />
              <button type="button" onClick={() => void enqueueReport()} className="rounded-2xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white">В очередь</button>
            </div>
            <div className="mt-4 space-y-3">
              <div className="rounded-2xl border border-purple-200 bg-purple-50 px-4 py-3">
                <div className="text-sm font-semibold text-purple-900">Текущий отчёт</div>
                <div className="mt-1 text-sm text-purple-800">{report.client_name || report.id}</div>
                <div className="mt-2 inline-flex items-center gap-1 rounded-full border border-purple-200 bg-white px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-purple-700">{statusIcon(report.status)} {prettyStatus(report.status)}</div>
              </div>
              {queue.map((item) => (
                <Link key={item.id} href={`/reports/${item.id}`} className="block rounded-2xl border border-slate-200 px-4 py-3 transition hover:border-slate-300 hover:bg-slate-50">
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0 text-sm font-semibold text-slate-900">{item.label}</div>
                    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${badgeTone(item.status)}`}>{statusIcon(item.status)} {prettyStatus(item.status)}</span>
                  </div>
                  <div className="mt-1 text-xs text-slate-500">Обновлён {formatDateTime(item.updatedAt)}</div>
                </Link>
              ))}
            </div>
          </div>
        </aside>
      </section>
    </div>
  );
}
