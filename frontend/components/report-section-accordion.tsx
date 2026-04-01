// ############################################################################
// AI_HEADER: MODULE_REPORT_SECTION_ACCORDION
// ROLE: Lazy-load report section content in an accordion.
// DEPENDENCIES: React, CopyButton.
// GRACE_ANCHORS: [SECTION_ACCORDION]
// ############################################################################

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, RefreshCw } from "lucide-react";

import CopyButton from "./copy-button";
import { ReportRenderer } from "./blocks/report-renderer";

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

type ReportSectionAccordionProps = {
  reportId: string;
  chunk: AdminReportChunk;
  meta: string;
  badgeClassName: string;
  errorAtLabel?: string | null;
  initiallyOpen?: boolean;
};

const statusLabel = (status: string) => {
  switch (status) {
    case "completed": return "done";
    case "in_progress": return "running";
    case "failed": return "error";
    default: return status || "pending";
  }
};

const parseBlocks = (content?: string | null) => {
  if (!content) return null;
  try {
    const parsed = JSON.parse(content);
    if (Array.isArray(parsed)) return parsed;
    if (parsed && typeof parsed === "object") return [parsed];
  } catch {}
  return null;
};

const extractPreview = (content?: string | null) => {
  if (!content) return null;
  const blocks = parseBlocks(content);
  if (blocks?.length) {
    const text = blocks
      .flatMap((block: any) => {
        if (typeof block?.text === "string") return [block.text];
        if (typeof block?.content === "string") return [block.content];
        if (typeof block?.body === "string") return [block.body];
        if (Array.isArray(block?.items)) return block.items.filter((item: unknown): item is string => typeof item === "string");
        return [];
      })
      .join(" ")
      .trim();
    return text.slice(0, 220) || null;
  }
  return content.replace(/\s+/g, " ").trim().slice(0, 220) || null;
};

export default function ReportSectionAccordion({
  reportId,
  chunk,
  meta,
  badgeClassName,
  errorAtLabel,
  initiallyOpen = false,
}: ReportSectionAccordionProps) {
  const [content, setContent] = useState<string | null>(chunk.content || null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(initiallyOpen);

  const hasContent = Boolean(content);
  const canLoad = chunk.status === "completed" && !hasContent && !loading;
  const blocks = useMemo(() => parseBlocks(content), [content]);
  const preview = useMemo(() => extractPreview(content || chunk.content), [chunk.content, content]);

  const loadContent = useCallback(async () => {
    if (!reportId || !chunk.section || loading) return;
    if (chunk.status !== "completed") return;
    if (hasContent) return;

    setLoading(true);
    setLoadError(null);
    try {
      const response = await fetch(`/api/admin/reports/${reportId}/sections/${chunk.section}`);
      if (!response.ok) throw new Error(`load_failed_${response.status}`);
      const data = (await response.json()) as AdminReportChunk;
      setContent(data.content || null);
    } catch {
      setLoadError("Не удалось загрузить контент. Попробуйте ещё раз.");
    } finally {
      setLoading(false);
    }
  }, [chunk.section, chunk.status, hasContent, loading, reportId]);

  useEffect(() => {
    if (!isOpen || !canLoad) return;
    void loadContent();
  }, [canLoad, isOpen, loadContent]);

  const runAction = useCallback(async (endpoint: string) => {
    setActionLoading(true);
    try {
      const response = await fetch(endpoint, { method: "POST" });
      if (!response.ok) throw new Error(`action_failed_${response.status}`);
    } catch {
      setLoadError("Команду не удалось отправить. Повторите попытку.");
    } finally {
      setActionLoading(false);
    }
  }, []);

  const sectionTitle = chunk.title || chunk.section;
  const showProgress = chunk.status === "in_progress";
  const canGenerate = ["pending", "failed"].includes(chunk.status);

  return (
    <details className="overflow-hidden rounded-3xl border border-slate-200 bg-slate-50" open={isOpen} onToggle={(event) => setIsOpen(event.currentTarget.open)}>
      <summary className="cursor-pointer list-none px-4 py-4 sm:px-5">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-base font-bold text-slate-900">{sectionTitle}</span>
              <span className={badgeClassName}>{statusLabel(chunk.status)}</span>
            </div>
            <div className="mt-1 text-xs text-slate-500">{meta}</div>
          </div>
          {preview ? <div className="max-w-xl text-sm leading-relaxed text-slate-500">{preview}</div> : null}
        </div>
      </summary>
      <div className="border-t border-slate-200 bg-white px-4 py-4 sm:px-5">
        {showProgress ? (
          <div className="mb-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            Секция сейчас в работе. После ответа модели блоки появятся здесь автоматически.
          </div>
        ) : null}
        <div className="mb-4 flex flex-wrap gap-2">
          <button type="button" onClick={() => void runAction(`/api/admin/reports/${reportId}/sections/${chunk.section}/regenerate/async`)} disabled={actionLoading} className="inline-flex items-center gap-2 rounded-2xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">
            {actionLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />} {canGenerate ? "Сгенерировать" : "Перегенерировать"}
          </button>
          <CopyButton text={content || chunk.content || ""} disabled={!content && !chunk.content} />
        </div>
        {chunk.error_message ? <div className="mb-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">Ошибка: {chunk.error_message}{errorAtLabel ? ` · ${errorAtLabel}` : ""}</div> : null}
        {loadError ? <div className="mb-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{loadError}</div> : null}
        {loading ? (
          <p className="text-sm text-slate-500">Загружаю блоки...</p>
        ) : blocks ? (
          <div className="report-blocks-container">
            <ReportRenderer blocks={blocks as any} fallbackText={content || chunk.content || undefined} />
          </div>
        ) : chunk.status === "completed" && (content || chunk.content) ? (
          <div data-testid="report-fallback-card" className="rounded-2xl border border-sky-200 bg-sky-50 px-4 py-4 text-sm leading-relaxed text-sky-900">
            {content || chunk.content}
          </div>
        ) : (
          <p className="text-sm text-slate-500">Мини-лог: контент появится после генерации секции.</p>
        )}
      </div>
    </details>
  );
}
