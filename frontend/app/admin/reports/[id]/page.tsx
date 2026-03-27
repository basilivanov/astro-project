"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  Clock3,
  Download,
  FileText,
  Loader2,
  Play,
  RefreshCw,
  ScrollText,
} from "lucide-react";

import { AdminNav } from "../../../../components/AdminNav";
import { RegenerateReportButton } from "../../../../components/admin/RegenerateReportButton";
import { ReportRenderer, type ReportBlock } from "../../../../components/blocks/report-renderer";
import { useTelegram } from "../../../../hooks/useTelegram";
import { trackEvent } from "../../../../lib/analytics";

export const dynamic = "force-dynamic";

type ReportStatus = "pending" | "running" | "done" | "error";

type ApiReport = {
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

type ApiChunk = {
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

type ApiRun = {
  id: string;
  status: string;
  error_message?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  total_tokens?: number | null;
  estimated_cost?: number | null;
  created_at: string;
};

type ApiReportDetail = {
  report: ApiReport;
  chunks: ApiChunk[];
  runs: ApiRun[];
  chart_svg?: string | null;
};

type AdminReportDeniedState = {
  role?: string;
  allowed_roles?: string[];
  task_href?: string;
  detail?: string;
};

type ReportQueueItem = {
  reportId: string;
  reportType: string;
  clientName: string;
  status: string;
  updatedAt?: string | null;
};

type SectionMeta = {
  section: string;
  title: string;
  order: number;
};

type ToastState = {
  kind: "error" | "success";
  text: string;
};

const STATUS_LABELS: Record<ReportStatus, string> = {
  pending: "в очереди",
  running: "в работе",
  done: "готово",
  error: "ошибка",
};

const FALLBACK_MARKERS = ["fallback", "заглуш", "template", "mock", "stub", "validation fallback"];

const SECTION_ORDER: SectionMeta[] = [
  { section: "input_frame", title: "1. Входная рамка", order: 0 },
  { section: "core_signature", title: "2. Ядро личности", order: 1 },
  { section: "life_vector", title: "3. Вектор жизни", order: 2 },
  { section: "strengths_resources", title: "4. Ресурсы и сильные стороны", order: 3 },
  { section: "shadow_growth", title: "5. Тени и рост", order: 4 },
  { section: "relationships", title: "6. Отношения", order: 5 },
  { section: "family_patterns", title: "7. Родовые и семейные сценарии", order: 6 },
  { section: "career_realization", title: "8. Карьера и реализация", order: 7 },
  { section: "money", title: "9. Деньги и опора", order: 8 },
  { section: "health_energy", title: "10. Энергия и ритм", order: 9 },
  { section: "spiritual_vector", title: "11. Смысл и духовный вектор", order: 10 },
  { section: "timing", title: "12. Временные акценты", order: 11 },
  { section: "practical_steps", title: "13. Практические шаги", order: 12 },
  { section: "executive_summary", title: "Краткое резюме", order: 13 },
  { section: "final_synthesis", title: "Финальный синтез", order: 14 },
];

const formatDateTime = (value?: string | null) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium", timeStyle: "short" }).format(date);
};

const mapStatus = (value?: string | null): ReportStatus => {
  switch (value) {
    case "completed":
    case "done":
      return "done";
    case "in_progress":
    case "running":
      return "running";
    case "failed":
    case "error":
      return "error";
    default:
      return "pending";
  }
};

const statusTone = (status: ReportStatus) => {
  switch (status) {
    case "done":
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    case "running":
      return "bg-amber-50 text-amber-700 border-amber-200";
    case "error":
      return "bg-rose-50 text-rose-700 border-rose-200";
    default:
      return "bg-slate-50 text-slate-600 border-slate-200";
  }
};

const parseBlocks = (content?: string | null): ReportBlock[] | null => {
  if (!content) return null;
  try {
    const parsed = JSON.parse(content);
    return Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
};

const compactText = (content?: string | null) => {
  if (!content) return "Пока нет текста.";
  const blocks = parseBlocks(content);
  if (blocks?.length) {
    const text = blocks
      .flatMap((block) => {
        if (typeof block?.text === "string") return [block.text];
        if (typeof block?.content === "string") return [block.content];
        if (Array.isArray(block?.items)) return block.items.map((item: unknown) => String(item));
        return [];
      })
      .join(" ")
      .replace(/\s+/g, " ")
      .trim();
    return text || "Структура готова, но текст пустой.";
  }
  return content.replace(/```[\s\S]*?```/g, "").replace(/\s+/g, " ").trim() || "Пока нет текста.";
};

const hasFallbackMarker = (content?: string | null) => {
  const normalized = (content || "").toLowerCase();
  return FALLBACK_MARKERS.some((marker) => normalized.includes(marker));
};

const logAdminEvent = (event: string, fields: Record<string, unknown> = {}) => {
  console.info(event, fields);
};

function SummaryCard({ title, content }: { title: string; content?: string | null }) {
  const fallback = hasFallbackMarker(content);
  return (
    <div className="rounded-3xl border border-slate-200 bg-white/95 p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between gap-3">
        <h3 className="text-sm font-bold text-slate-900">{title}</h3>
        {fallback ? (
          <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-[11px] font-semibold text-amber-700">
            Есть fallback-маркер
          </span>
        ) : null}
      </div>
      <p className="text-sm leading-6 text-slate-700">{compactText(content)}</p>
    </div>
  );
}

function InlineToast({ toast }: { toast: ToastState }) {
  const tone = toast.kind === "error"
    ? "border-rose-200 bg-rose-50 text-rose-700"
    : "border-emerald-200 bg-emerald-50 text-emerald-700";

  return (
    <div
      className={`fixed right-4 top-4 z-50 flex max-w-sm items-start gap-3 rounded-2xl border px-4 py-3 text-sm shadow-lg ${tone}`}
      role="status"
      aria-live="polite"
      data-testid="admin-toast"
    >
      {toast.kind === "error" ? <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> : <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />}
      <span>{toast.text}</span>
    </div>
  );
}

function EventLog({ runs }: { runs: ApiRun[] }) {
  return (
    <section className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
      <div className="mb-4 flex items-center gap-2">
        <ScrollText className="h-4 w-4 text-slate-500" />
        <h2 className="text-lg font-bold text-slate-900">Журнал событий</h2>
      </div>
      <div className="space-y-3">
        {runs.length === 0 ? (
          <p className="text-sm text-slate-500">Запусков пока нет.</p>
        ) : (
          runs.map((run, index) => {
            const status = mapStatus(run.status);
            return (
              <div key={run.id} className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-semibold text-slate-900">Запуск #{runs.length - index}</div>
                  <span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ${statusTone(status)}`}>
                    {STATUS_LABELS[status]}
                  </span>
                </div>
                <div className="text-xs leading-5 text-slate-600">
                  Создан: {formatDateTime(run.created_at)} · Старт: {formatDateTime(run.started_at)} · Финиш: {formatDateTime(run.finished_at)}
                </div>
                <div className="mt-1 text-xs leading-5 text-slate-600">
                  Токены: {run.total_tokens ?? "—"} · Стоимость: {typeof run.estimated_cost === "number" ? run.estimated_cost.toFixed(4) : "—"}
                </div>
                {run.error_message ? <div className="mt-2 text-sm text-rose-600">{run.error_message}</div> : null}
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

function SectionCard({
  reportId,
  chunk,
  initiallyOpen,
  onRefresh,
  onSectionGenerate,
}: {
  reportId: string;
  chunk: ApiChunk;
  initiallyOpen: boolean;
  onRefresh: () => Promise<void>;
  onSectionGenerate: (sectionId: string) => Promise<void>;
}) {
  const [open, setOpen] = useState(initiallyOpen);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const status = mapStatus(chunk.status);
  const blocks = useMemo(() => parseBlocks(chunk.content), [chunk.content]);
  const previewText = useMemo(() => compactText(chunk.content), [chunk.content]);

  const handleGenerate = async () => {
    setIsSubmitting(true);
    try {
      await onSectionGenerate(chunk.section);
      await onRefresh();
    } finally {
      setIsSubmitting(false);
      setOpen(true);
    }
  };

  return (
    <details
      open={open}
      onToggle={(event) => setOpen(event.currentTarget.open)}
      className="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-sm"
      data-testid={`admin-section-${chunk.section}`}
    >
      <summary className="flex cursor-pointer list-none flex-col gap-3 px-4 py-4 sm:px-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-base font-bold text-slate-900 sm:text-lg">{chunk.title || chunk.section}</h3>
              <span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ${statusTone(status)}`}>
                {STATUS_LABELS[status]}
              </span>
            </div>
            <p className="mt-1 text-sm leading-6 text-slate-500">
              Секция #{chunk.order_index + 1} · {chunk.section} · Обновлено {formatDateTime(chunk.created_at)}
            </p>
          </div>
          <ChevronDown className="h-5 w-5 shrink-0 text-slate-400 transition-transform group-open:rotate-180" />
        </div>
        <p className="line-clamp-2 text-sm leading-6 text-slate-700">{previewText}</p>
      </summary>
      <div className="border-t border-slate-100 px-4 py-4 sm:px-6">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleGenerate}
            disabled={isSubmitting}
            className="inline-flex min-h-10 items-center gap-2 rounded-2xl bg-purple-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-60"
            data-testid={`admin-generate-section-${chunk.section}`}
          >
            {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : status === "done" ? <RefreshCw className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {status === "done" ? "Перегенерировать" : "Сгенерировать"}
          </button>
          <RegenerateReportButton reportId={reportId} />
        </div>
        {chunk.error_message ? (
          <div className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            Ошибка: {chunk.error_message}
          </div>
        ) : null}
        <div className="mb-4 rounded-2xl border border-slate-200 bg-slate-50/70 p-4 text-sm leading-6 text-slate-600">
          <div className="mb-2 font-semibold text-slate-900">Мини-лог</div>
          <div>Статус: {STATUS_LABELS[status]}.</div>
          <div>Последнее обновление: {formatDateTime(chunk.created_at)}.</div>
          <div>Ошибка: {chunk.error_message || "не было"}.</div>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-4">
          {blocks?.length ? (
            <ReportRenderer blocks={blocks} fallbackText={chunk.content} />
          ) : (
            <p className="text-sm leading-6 text-slate-600">Контент появится после генерации секции.</p>
          )}
        </div>
      </div>
    </details>
  );
}

export default function AdminNatalMasterPage() {
  const { initData, isReady } = useTelegram();
  const [reports, setReports] = useState<ApiReport[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [detail, setDetail] = useState<ApiReportDetail | null>(null);
  const [deniedState, setDeniedState] = useState<AdminReportDeniedState | null>(null);
  const [loading, setLoading] = useState(true);
  const [queueLoading, setQueueLoading] = useState(true);
  const [globalRunning, setGlobalRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastState | null>(null);

  const showToast = useCallback((kind: ToastState["kind"], text: string) => {
    setToast({ kind, text });
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 4000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const fetchQueue = useCallback(async () => {
    if (!isReady) return;
    setQueueLoading(true);
    try {
      logAdminEvent("admin.queue", { stage: "fetch_list_start", reportId: selectedId ?? null });
      const url = new URL("/api/admin/reports", window.location.origin);
      url.searchParams.set("limit", "25");
      const response = await fetch(url.toString(), { headers: { "X-Telegram-Auth": initData } });
      if (!response.ok) throw new Error(`queue ${response.status}`);
      const data = (await response.json()) as ApiReport[];
      const natalReports = data.filter((item) => item.report_type === "natal_master");
      setReports(natalReports);
      logAdminEvent("admin.queue", { stage: "fetch_list_done", reportId: selectedId ?? null, queueSize: natalReports.length });
      if (!selectedId && natalReports[0]?.id) setSelectedId(natalReports[0].id);
    } catch (error) {
      console.error(error);
      logAdminEvent("admin.error", { stage: "fetch_list_failed", reportId: selectedId ?? null });
      setMessage("Не удалось загрузить очередь отчётов.");
      showToast("error", "Не удалось загрузить очередь отчётов.");
    } finally {
      setQueueLoading(false);
    }
  }, [initData, isReady, selectedId, showToast]);

  const fetchDetail = useCallback(async () => {
    if (!selectedId || !isReady) return;
    setLoading(true);
    try {
      logAdminEvent("admin.entry", { stage: "detail_fetch_start", reportId: selectedId });
      const response = await fetch(`/api/admin/reports/${selectedId}?include_content=1`, {
        headers: { "X-Telegram-Auth": initData },
      });
      if (!response.ok) {
        if (response.status === 403) {
          const payload = await response.json().catch(() => ({}));
          const nextDeniedState: AdminReportDeniedState = {
            role: typeof payload?.role === "string" ? payload.role : undefined,
            allowed_roles: Array.isArray(payload?.allowed_roles) ? payload.allowed_roles : undefined,
            task_href: typeof payload?.task_href === "string" ? payload.task_href : "/Task.md",
            detail: typeof payload?.detail === "string" ? payload.detail : "forbidden",
          };
          setDetail(null);
          setDeniedState(nextDeniedState);
          void trackEvent("admin.report_detail_rbac_denied", {
            role: nextDeniedState.role ?? "unknown",
            allowed_roles: nextDeniedState.allowed_roles ?? [],
            target_path: `/admin/reports/${selectedId}`,
            task_href: nextDeniedState.task_href,
            block: "REPORT_DETAIL_RBAC_DENIED",
            semantic_block: "REPORT_DETAIL_RBAC_DENIED",
            surface: "admin_report_detail",
          }, {
            flowId: "FLOW-ADMIN-OPS",
            block: "REPORT_DETAIL_RBAC_DENIED",
            semanticBlock: "REPORT_DETAIL_RBAC_DENIED",
          });
          return;
        }
        throw new Error(`detail ${response.status}`);
      }
      const data = (await response.json()) as ApiReportDetail;
      setDeniedState(null);
      const sectionMap = new Map(SECTION_ORDER.map((item) => [item.section, item]));
      const normalizedChunks = [...data.chunks].sort((a, b) => {
        const aOrder = sectionMap.get(a.section)?.order ?? a.order_index;
        const bOrder = sectionMap.get(b.section)?.order ?? b.order_index;
        return aOrder - bOrder;
      });
      setDetail({ ...data, chunks: normalizedChunks });
      logAdminEvent("admin.entry", { stage: "detail_fetch_done", reportId: selectedId, sections: normalizedChunks.map((chunk) => chunk.section), fallbackSections: normalizedChunks.filter((chunk) => hasFallbackMarker(chunk.content)).map((chunk) => chunk.section) });
    } catch (error) {
      console.error(error);
      logAdminEvent("admin.error", { stage: "detail_fetch_failed", reportId: selectedId });
      setMessage("Не удалось загрузить отчёт.");
      showToast("error", "Не удалось загрузить отчёт.");
    } finally {
      setLoading(false);
    }
  }, [initData, isReady, selectedId, showToast]);

  useEffect(() => {
    void fetchQueue();
  }, [fetchQueue]);

  useEffect(() => {
    void fetchDetail();
  }, [fetchDetail]);

  useEffect(() => {
    if (!detail) return;
    if (!["in_progress", "pending"].includes(detail.report.status)) return;
    const timer = window.setInterval(() => {
      void fetchDetail();
      void fetchQueue();
    }, 4000);
    return () => window.clearInterval(timer);
  }, [detail, fetchDetail, fetchQueue]);

  const report = detail?.report;
  const chunks = detail?.chunks ?? [];
  const runs = detail?.runs ?? [];
  const summaryChunk = chunks.find((item) => item.section === "executive_summary");
  const synthesisChunk = chunks.find((item) => item.section === "final_synthesis");
  const visibleChunks = chunks.filter((item) => !["executive_summary", "final_synthesis"].includes(item.section));
  const completed = chunks.filter((item) => mapStatus(item.status) === "done").length;
  const progressPercent = chunks.length ? Math.round((completed / chunks.length) * 100) : 0;

  const generateSection = useCallback(
    async (sectionId: string) => {
      if (!selectedId) return;
      logAdminEvent("admin.section_regenerate", { stage: "request", reportId: selectedId, sectionId });
      const response = await fetch(`/api/admin/reports/${selectedId}/sections/${sectionId}/regenerate/async`, {
        method: "POST",
        headers: { "X-Telegram-Auth": initData },
      });
      if (!response.ok) {
        logAdminEvent("admin.error", { stage: "section_regenerate_failed", reportId: selectedId, sectionId, status: response.status });
        setMessage("Не удалось запустить генерацию секции.");
        showToast("error", "Не удалось запустить генерацию секции.");
        throw new Error(`section ${response.status}`);
      }
      logAdminEvent("admin.section_regenerate", { stage: "queued", reportId: selectedId, sectionId });
      setMessage(`Секция «${sectionId}» добавлена в очередь.`);
      showToast("success", `Секция «${sectionId}» добавлена в очередь.`);
    },
    [initData, selectedId, showToast]
  );

  const generateAll = useCallback(async () => {
    if (!selectedId || globalRunning) return;
    setGlobalRunning(true);
    setMessage(null);
    try {
      for (const chunk of chunks) {
        logAdminEvent("admin.section_regenerate", { stage: "bulk_request", reportId: selectedId, sectionId: chunk.section });
        await fetch(`/api/admin/reports/${selectedId}/sections/${chunk.section}/regenerate/async`, {
          method: "POST",
          headers: { "X-Telegram-Auth": initData },
        });
        setMessage(`В очереди: ${chunk.title || chunk.section}`);
        await new Promise((resolve) => window.setTimeout(resolve, 350));
      }
      logAdminEvent("admin.queue", { stage: "bulk_queued", reportId: selectedId, sections: chunks.map((chunk) => chunk.section) });
      setMessage("Все секции поставлены в последовательную очередь.");
      showToast("success", "Все секции поставлены в последовательную очередь.");
      await fetchDetail();
      await fetchQueue();
    } catch (error) {
      console.error(error);
      logAdminEvent("admin.error", { stage: "bulk_regenerate_failed", reportId: selectedId });
      setMessage("Не удалось поставить все секции в очередь.");
      showToast("error", "Не удалось поставить все секции в очередь.");
    } finally {
      setGlobalRunning(false);
    }
  }, [chunks, fetchDetail, fetchQueue, globalRunning, initData, selectedId, showToast]);

  const downloadExport = async (format: "md" | "pdf") => {
    if (!selectedId) return;
    logAdminEvent("admin.export", { stage: "request", reportId: selectedId, format });
    const response = await fetch(`/api/admin/reports/${selectedId}/export?format=${format}`, {
      headers: { "X-Telegram-Auth": initData },
    });
    if (!response.ok) {
      logAdminEvent("admin.error", { stage: "export_failed", reportId: selectedId, format, status: response.status });
      setMessage(`Не удалось скачать ${format === "md" ? "Markdown" : "PDF"}.`);
      showToast("error", `Не удалось скачать ${format === "md" ? "Markdown" : "PDF"}.`);
      return;
    }
    const blob = await response.blob();
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = `${selectedId}.${format === "md" ? "md" : "pdf"}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(href);
    logAdminEvent("admin.export", { stage: "download_started", reportId: selectedId, format });
    showToast("success", `${format === "md" ? "Markdown" : "PDF"} скачивается.`);
  };

  const queueItems: ReportQueueItem[] = useMemo(
    () =>
      reports.map((item) => ({
        reportId: item.id,
        reportType: item.report_type,
        clientName: item.client_name,
        status: item.status,
        updatedAt: item.updated_at,
      })),
    [reports]
  );

  if (deniedState) {
    return (
      <div className="min-h-screen bg-slate-50">
        <AdminNav />
        <main className="pb-24 md:pl-64">
          <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-3 py-4 sm:px-4 sm:py-6 lg:px-6">
            <section className="rounded-[28px] border border-amber-200 bg-amber-50 px-5 py-5 text-amber-900 shadow-sm" data-testid="admin-report-detail-denied">
              <h1 className="text-xl font-bold">Доступ ограничен</h1>
              <p className="mt-2 text-sm">Детали отчета доступны только администраторам.</p>
              <p className="mt-1 text-sm">Текущая роль: {deniedState.role ?? "unknown"}.</p>
              <Link href={deniedState.task_href ?? "/Task.md"} className="mt-4 inline-flex text-sm font-semibold underline underline-offset-4">
                Task.md
              </Link>
            </section>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {toast ? <InlineToast toast={toast} /> : null}
      <AdminNav />
      <main className="pb-24 md:pl-64">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-3 py-4 sm:px-4 sm:py-6 lg:px-6">
          <section className="sticky top-0 z-20 rounded-[28px] border border-slate-200 bg-white/95 p-4 shadow-sm backdrop-blur sm:p-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className="rounded-full border border-purple-200 bg-purple-50 px-3 py-1 text-xs font-semibold text-purple-700">
                    Админка natal_master
                  </span>
                  {report ? (
                    <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${statusTone(mapStatus(report.status))}`}>
                      {STATUS_LABELS[mapStatus(report.status)]}
                    </span>
                  ) : null}
                </div>
                <h1 className="text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">
                  Запуск, контроль и выгрузка natal_master
                </h1>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
                  Из этой страницы можно пройти отчёт по секциям, следить за очередью, смотреть превью и скачивать собранный результат.
                </p>
                {report ? (
                  <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-500 sm:text-sm">
                    <span>Клиент: {report.client_name || "—"}</span>
                    <span>ID: {report.id}</span>
                    <span>Создан: {formatDateTime(report.created_at)}</span>
                  </div>
                ) : null}
              </div>
              <div className="flex w-full flex-col gap-2 sm:flex-row sm:flex-wrap lg:w-auto lg:max-w-md">
                <button
                  type="button"
                  onClick={generateAll}
                  disabled={!chunks.length || globalRunning}
                  className="inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl bg-purple-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-60"
                  data-testid="admin-generate-all"
                >
                  {globalRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  Сгенерить всё
                </button>
                <button
                  type="button"
                  onClick={() => void downloadExport("md")}
                  disabled={!selectedId}
                  data-testid="admin-download-markdown"
                  className="inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-300 disabled:opacity-60"
                >
                  <Download className="h-4 w-4" />Скачать Markdown
                </button>
                <button
                  type="button"
                  onClick={() => void downloadExport("pdf")}
                  disabled={!selectedId}
                  data-testid="admin-download-pdf"
                  className="inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-300 disabled:opacity-60"
                >
                  <FileText className="h-4 w-4" />Скачать PDF
                </button>
              </div>
            </div>
            <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(280px,0.8fr)]">
              <div>
                <div className="mb-2 flex items-center justify-between text-sm font-semibold text-slate-700">
                  <span>Прогресс отчёта</span>
                  <span>{completed}/{chunks.length || 0}</span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-slate-100" role="progressbar" aria-valuenow={progressPercent}>
                  <div className="h-full rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all" style={{ width: `${progressPercent}%` }} />
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-500 sm:text-sm">
                  <span className="inline-flex items-center gap-1"><CheckCircle2 className="h-4 w-4 text-emerald-600" />Готово: {chunks.filter((item) => mapStatus(item.status) === "done").length}</span>
                  <span className="inline-flex items-center gap-1"><Loader2 className="h-4 w-4 text-amber-600" />В работе: {chunks.filter((item) => mapStatus(item.status) === "running").length}</span>
                  <span className="inline-flex items-center gap-1"><AlertCircle className="h-4 w-4 text-rose-600" />Ошибок: {chunks.filter((item) => mapStatus(item.status) === "error").length}</span>
                </div>
                {message ? <div className="mt-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">{message}</div> : null}
              </div>
              <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-4">
                <div className="mb-2 text-sm font-bold text-slate-900">Очередь отчётов</div>
                {queueLoading ? (
                  <div className="text-sm text-slate-500">Загружаю очередь…</div>
                ) : queueItems.length === 0 ? (
                  <div className="text-sm text-slate-500">Отчётов natal_master пока нет.</div>
                ) : (
                  <div className="space-y-2">
                    {queueItems.map((item) => (
                      <button
                        key={item.reportId}
                        type="button"
                        onClick={() => setSelectedId(item.reportId)}
                        className={`flex w-full items-center justify-between rounded-2xl border px-3 py-3 text-left transition ${selectedId === item.reportId ? "border-purple-300 bg-white shadow-sm" : "border-slate-200 bg-white/80 hover:border-slate-300"}`}
                      >
                        <div className="min-w-0">
                          <div className="truncate text-sm font-semibold text-slate-900">{item.clientName || "Без имени"}</div>
                          <div className="text-xs text-slate-500">{formatDateTime(item.updatedAt)} · {item.reportId.slice(0, 8)}</div>
                        </div>
                        <span className={`rounded-full border px-2 py-1 text-[11px] font-semibold uppercase tracking-wide ${statusTone(mapStatus(item.status))}`}>
                          {STATUS_LABELS[mapStatus(item.status)]}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </section>

          {loading ? (
            <div className="rounded-[28px] border border-slate-200 bg-white p-8 text-center text-slate-500 shadow-sm">Загружаю отчёт…</div>
          ) : !detail ? (
            <div className="rounded-[28px] border border-slate-200 bg-white p-8 text-center text-slate-500 shadow-sm">Выберите отчёт из очереди.</div>
          ) : (
            <>
              <section className="grid gap-4 lg:grid-cols-2">
                <SummaryCard title="Краткий итог" content={summaryChunk?.content} />
                <SummaryCard title="Финальный синтез" content={synthesisChunk?.content} />
              </section>

              <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
                <div className="space-y-4">
                  {visibleChunks.map((chunk, index) => (
                    <SectionCard
                      key={chunk.id}
                      reportId={detail.report.id}
                      chunk={chunk}
                      initiallyOpen={index < 3}
                      onRefresh={fetchDetail}
                      onSectionGenerate={generateSection}
                    />
                  ))}
                </div>
                <aside className="space-y-4">
                  {detail.chart_svg ? (
                    <section className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm">
                      <h2 className="mb-3 text-base font-bold text-slate-900">Карта</h2>
                      <div className="overflow-hidden rounded-3xl border border-slate-100 bg-slate-50 p-2" dangerouslySetInnerHTML={{ __html: detail.chart_svg }} />
                    </section>
                  ) : null}
                  <section className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm">
                    <h2 className="mb-3 text-base font-bold text-slate-900">Быстрые действия</h2>
                    <div className="space-y-2 text-sm text-slate-600">
                      <Link href="/admin/reports" className="flex items-center gap-2 rounded-2xl border border-slate-200 px-3 py-3 hover:border-slate-300">
                        <Clock3 className="h-4 w-4" />К списку отчётов
                      </Link>
                      <Link href={`/reports/${detail.report.id}`} className="flex items-center gap-2 rounded-2xl border border-slate-200 px-3 py-3 hover:border-slate-300">
                        <FileText className="h-4 w-4" />Открыть текущую страницу отчёта
                      </Link>
                    </div>
                  </section>
                </aside>
              </section>

              <EventLog runs={runs} />
            </>
          )}
        </div>
      </main>
    </div>
  );
}
