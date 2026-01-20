// ############################################################################
// AI_HEADER: MODULE_REPORT_SECTION_ACCORDION
// ROLE: Lazy-load report section content in an accordion.
// DEPENDENCIES: React, CopyButton.
// GRACE_ANCHORS: [SECTION_ACCORDION]
// ############################################################################

"use client";

import { useCallback, useEffect, useState } from "react";

import CopyButton from "./copy-button";

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
  regenerateAction: (formData: FormData) => void;
};

const statusLabel = (status: string) => status || "unknown";

export default function ReportSectionAccordion({
  reportId,
  chunk,
  meta,
  badgeClassName,
  errorAtLabel,
  regenerateAction,
}: ReportSectionAccordionProps) {
  const [content, setContent] = useState<string | null>(chunk.content || null);
  const [contentHtml, setContentHtml] = useState<string | null>(
    chunk.content_html || null
  );
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const hasContent = Boolean(contentHtml || content);
  const canLoad = chunk.status === "completed" && !hasContent && !loading;

  const loadContent = useCallback(async () => {
    if (!reportId || !chunk.section || loading) return;
    if (chunk.status !== "completed") return;
    if (hasContent) return;

    setLoading(true);
    setLoadError(null);
    try {
      const response = await fetch(
        `/api/admin/reports/${reportId}/sections/${chunk.section}`
      );
      if (!response.ok) {
        throw new Error(`load failed: ${response.status}`);
      }
      const data = (await response.json()) as AdminReportChunk;
      setContent(data.content || null);
      setContentHtml(data.content_html || null);
    } catch (err) {
      console.error(err);
      setLoadError("Не удалось загрузить контент. Попробуйте еще раз.");
    } finally {
      setLoading(false);
    }
  }, [chunk.section, chunk.status, hasContent, loading, reportId]);

  useEffect(() => {
    if (!isOpen) return;
    if (!canLoad) return;
    void loadContent();
  }, [canLoad, isOpen, loadContent]);

  const sectionTitle = chunk.title || chunk.section;
  const showProgress = chunk.status === "in_progress";

  return (
    <details
      className="accordion"
      onToggle={(event) => {
        setIsOpen(event.currentTarget.open);
      }}
    >
      <summary className="accordion__summary">
        <div className="accordion__title">
          <div className="accordion__label-row">
            <span className="accordion__label">{sectionTitle}</span>
            <span className={badgeClassName}>{statusLabel(chunk.status)}</span>
          </div>
          <span className="accordion__chevron" aria-hidden="true">
            {">"}
          </span>
        </div>
        <span className="accordion__meta">{meta}</span>
      </summary>
      <div className="accordion__content">
        {showProgress ? (
          <div className="section-progress">
            <div className="section-progress__label">Генерация секции...</div>
            <div className="section-progress__bar" role="progressbar">
              <div className="section-progress__fill" />
            </div>
          </div>
        ) : null}
        <div className="accordion__actions">
          <form action={regenerateAction}>
            <input type="hidden" name="report_id" value={reportId} />
            <input type="hidden" name="section_id" value={chunk.section} />
            <button className="btn btn-secondary" type="submit">
              Перегенерить
            </button>
          </form>
          <CopyButton text={content || ""} disabled={!content} />
        </div>
        {chunk.error_message ? (
          <div className="text-sm text-[var(--accent-3)]">
            Ошибка: {chunk.error_message}
            {errorAtLabel ? ` · ${errorAtLabel}` : ""}
          </div>
        ) : null}
        {loadError ? (
          <div className="text-sm text-[var(--accent-3)]">{loadError}</div>
        ) : null}
        {loading ? (
          <p className="subtle text-sm">Загружаю контент...</p>
        ) : contentHtml ? (
          <div
            className="report-content"
            dangerouslySetInnerHTML={{ __html: contentHtml }}
          />
        ) : content ? (
          <p className="text-sm whitespace-pre-wrap break-words">{content}</p>
        ) : chunk.status === "completed" ? (
          <p className="subtle text-sm">Контент пока не загружен.</p>
        ) : (
          <p className="subtle text-sm">Контент будет доступен после генерации.</p>
        )}
      </div>
    </details>
  );
}
