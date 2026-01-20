// ############################################################################
// AI_HEADER: MODULE_ADMIN_REPORT_DETAIL
// ROLE: Admin report detail view.
// DEPENDENCIES: backend admin API.
// GRACE_ANCHORS: [TYPES, DATA_CONFIG, SERVER_ACTIONS, UI_UTILS, PROGRESS_LOGIC, DATA_FETCH, PAGE_RENDER]
// ############################################################################

import { redirect } from "next/navigation";
import { headers } from "next/headers";

import ReportStatusPoller from "../../../components/report-status-poller";
import ReportSectionAccordion from "../../../components/report-section-accordion";

export const dynamic = "force-dynamic";

// #START_BLOCK_TYPES
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
  created_at: string;
};

type AdminReportDetail = {
  report: AdminReport;
  chunks: AdminReportChunk[];
  runs: AdminReportRun[];
  markdown?: string | null;
};
// #END_BLOCK_TYPES

// #START_BLOCK_DATA_CONFIG
const resolveApiBase = () => {
  const internal = process.env.INTERNAL_API_URL?.replace(/\/$/, "");
  if (internal) return internal;

  const publicBase = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (publicBase) return publicBase;

  const headerList = headers();
  const host = headerList.get("x-forwarded-host") || headerList.get("host");
  const proto = headerList.get("x-forwarded-proto") || "http";
  if (host) {
    return `${proto}://${host}`;
  }

  return "http://backend:8000";
};
// #END_BLOCK_DATA_CONFIG

// #START_BLOCK_SERVER_ACTIONS
async function regenerateAll(formData: FormData) {
  "use server";

  const reportId = String(formData.get("report_id") || "");
  if (!reportId) return;

  const response = await fetch(
    `${resolveApiBase()}/api/admin/reports/${reportId}/regenerate/async`,
    { method: "POST" }
  );

  if (!response.ok) {
    let message = `Ошибка API: ${response.status}`;
    try {
      const data = await response.json();
      if (data?.detail) {
        message = String(data.detail);
      }
    } catch {
      // ignore parse errors, keep fallback message
    }
    redirect(`/reports/${reportId}?error=${encodeURIComponent(message)}`);
  }

  redirect(`/reports/${reportId}`);
}

async function regenerateSection(formData: FormData) {
  "use server";

  const reportId = String(formData.get("report_id") || "");
  const sectionId = String(formData.get("section_id") || "");
  if (!reportId || !sectionId) return;

  const response = await fetch(
    `${resolveApiBase()}/api/admin/reports/${reportId}/sections/${sectionId}/regenerate/async`,
    { method: "POST" }
  );

  if (!response.ok) {
    let message = `Ошибка API: ${response.status}`;
    try {
      const data = await response.json();
      if (data?.detail) {
        message = String(data.detail);
      }
    } catch {
      // ignore parse errors, keep fallback message
    }
    redirect(`/reports/${reportId}?error=${encodeURIComponent(message)}`);
  }

  redirect(`/reports/${reportId}`);
}
// #END_BLOCK_SERVER_ACTIONS

// #START_BLOCK_UI_UTILS
const formatDateTime = (value?: string | null) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
};

const formatReportType = (value: string) =>
  value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());

const reportBadge = (status: string) => {
  switch (status) {
    case "completed":
      return "badge badge--ok";
    case "in_progress":
      return "badge badge--warn";
    case "failed":
      return "badge badge--hot";
    default:
      return "badge badge--cold";
  }
};

// #END_BLOCK_UI_UTILS

// #START_BLOCK_PROGRESS_LOGIC
const buildProgress = (report: AdminReport, chunks: AdminReportChunk[]) => {
  const sectionChunks = chunks.filter((chunk) => chunk.section !== "final_markdown");
  const total = sectionChunks.length;
  const completed = sectionChunks.filter((chunk) => chunk.status === "completed").length;
  const failedChunk = sectionChunks.find((chunk) => chunk.status === "failed");
  const inProgressChunk = sectionChunks.find((chunk) => chunk.status === "in_progress");
  const markdownChunk = chunks.find((chunk) => chunk.section === "final_markdown");
  const isFinalizing = markdownChunk?.status === "in_progress";

  let percent = total > 0 ? Math.round((completed / total) * 100) : 0;
  if (report.status === "completed") {
    percent = 100;
  } else if (report.status === "in_progress" && total === 0) {
    percent = 8;
  }
  if (report.status !== "completed") {
    percent = Math.min(98, Math.max(percent, report.status === "in_progress" ? 6 : 0));
  }

  let label = "Запуск";
  let detail = "Готовим список секций для генерации.";
  if (report.status === "failed" || failedChunk) {
    label = "Ошибка генерации";
    detail = "Проверьте логи или перегенерируйте секцию.";
  } else if (report.status === "completed") {
    label = "Готово";
    detail = `Секции: ${completed}/${total}.`;
  } else if (isFinalizing) {
    label = "Собираю Markdown";
    detail = "Финальная сборка отчета.";
  } else if (inProgressChunk) {
    const title = inProgressChunk.title || inProgressChunk.section;
    label = `Запрашиваю и записываю секцию: ${title}`;
    detail = `Секции: ${completed}/${total}.`;
  } else if (total > 0 && completed > 0) {
    label = "Готовлю следующую секцию";
    detail = `Секции: ${completed}/${total}.`;
  } else if (total > 0) {
    label = "Запускаю генерацию";
    detail = "Подготовка секций к запросам.";
  }

  const tone =
    report.status === "failed" || failedChunk
      ? "progress__fill--fail"
      : report.status === "completed"
      ? "progress__fill--ok"
      : "progress__fill--warn";

  return {
    percent,
    label,
    detail,
    tone,
    total,
    completed,
  };
};
// #END_BLOCK_PROGRESS_LOGIC

// #START_BLOCK_DATA_FETCH
async function fetchReport(reportId: string): Promise<AdminReportDetail> {
  const response = await fetch(
    `${resolveApiBase()}/api/admin/reports/${reportId}?include_content=0`,
    { cache: "no-store" }
  );
  if (!response.ok) {
    throw new Error(`Report fetch failed: ${response.status}`);
  }
  return response.json() as Promise<AdminReportDetail>;
}
// #END_BLOCK_DATA_FETCH

// #START_BLOCK_PAGE_RENDER
export default async function Page({
  params,
  searchParams,
}: {
  params: { id: string };
  searchParams?: { error?: string | string[] };
}) {
  const errorParam = searchParams?.error;
  const errorMessage = Array.isArray(errorParam) ? errorParam[0] : errorParam;
  try {
    const data = await fetchReport(params.id);
    const { report, chunks, runs } = data;
    const runItems = runs || [];
    const progress = buildProgress(report, chunks);

    return (
      <main className="page">
        <div className="mx-auto flex max-w-5xl flex-col gap-8 px-5 py-8 sm:px-6 sm:py-12">
          <ReportStatusPoller reportId={report.id} status={report.status} />
          <header className="flex flex-col gap-4">
            <div className="eyebrow">Отчет</div>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <h1 className="text-2xl sm:text-3xl md:text-4xl">
                {formatReportType(report.report_type)}
              </h1>
              <span className={reportBadge(report.status)}>{report.status}</span>
            </div>
            <p className="subtle text-sm">
              Клиент: {report.client_name} · Создан: {formatDateTime(report.created_at)}
            </p>
            {errorMessage ? (
              <div className="text-sm text-[var(--accent-3)]">{errorMessage}</div>
            ) : null}
            {report.error_message ? (
              <div className="text-sm text-[var(--accent-3)]">
                Ошибка: {report.error_message} · {formatDateTime(report.error_at)}
              </div>
            ) : null}
            <div className="progress-card">
              <div className="progress__header">
                <div className="progress__label">{progress.label}</div>
                <div className="progress__detail">{progress.detail}</div>
              </div>
              <div className="progress__bar" role="progressbar">
                <div
                  className={`progress__fill ${progress.tone}`}
                  style={{ width: `${progress.percent}%` }}
                />
              </div>
              <div className="progress__meta">
                {progress.completed}/{progress.total} секций · {progress.percent}%
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <a className="btn btn-secondary" href="/admin">
                Назад к дашборду
              </a>
              <a
                className="btn btn-secondary"
                href={`/api/admin/reports/${report.id}/pdf`}
                target="_blank"
                rel="noreferrer"
              >
                Скачать PDF
              </a>
              <form action={regenerateAll}>
                <input type="hidden" name="report_id" value={report.id} />
                <button className="btn btn-primary" type="submit">
                  Сгенерировать все
                </button>
              </form>
            </div>
          </header>

          <section className="grid gap-6">
            <div className="card flex flex-col gap-4 p-6">
              <h2 className="text-2xl">Секции</h2>
              {chunks.length === 0 ? (
                <p className="subtle text-sm">Секции пока отсутствуют.</p>
              ) : (
                <div className="flex flex-col gap-4">
                  {chunks
                    .filter((chunk) => chunk.section !== "final_markdown")
                    .map((chunk) => {
                      const meta = `#${chunk.order_index + 1} · ${formatDateTime(
                        chunk.created_at
                      )} · ${chunk.section}`;
                      return (
                        <ReportSectionAccordion
                          key={chunk.id}
                          reportId={report.id}
                          chunk={chunk}
                          meta={meta}
                          badgeClassName={reportBadge(chunk.status)}
                          errorAtLabel={formatDateTime(chunk.error_at)}
                          regenerateAction={regenerateSection}
                        />
                      );
                    })}
                </div>
                )}
            </div>
            {runItems.length > 0 ? (
              <details className="card flex flex-col gap-4 p-6">
                <summary className="accordion__summary">
                  <div className="accordion__title">
                    <div className="accordion__label-row">
                      <span className="accordion__label">Технические детали</span>
                      <span className="badge badge--cold">Запуски</span>
                    </div>
                    <span className="accordion__chevron" aria-hidden="true">
                      {">"}
                    </span>
                  </div>
                  <span className="accordion__meta">История запусков отчета</span>
                </summary>
                <div className="accordion__content">
                  <div className="flex flex-col gap-3">
                    {runItems.map((run, index) => (
                      <div
                        key={run.id}
                        className="rounded-2xl border border-white/10 p-4"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="text-sm font-semibold">
                            Запуск #{runItems.length - index}
                          </div>
                          <span className={reportBadge(run.status)}>{run.status}</span>
                        </div>
                        <div className="subtle text-sm">
                          Создан: {formatDateTime(run.created_at)} · Старт:{" "}
                          {formatDateTime(run.started_at)} · Финиш:{" "}
                          {formatDateTime(run.finished_at)}
                        </div>
                        {run.error_message ? (
                          <div className="text-sm text-[var(--accent-3)]">
                            Ошибка: {run.error_message}
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>
              </details>
            ) : null}
          </section>
        </div>
      </main>
    );
  } catch (error) {
    return (
      <main className="page">
        <div className="mx-auto flex max-w-3xl flex-col gap-6 px-5 py-8 sm:px-6 sm:py-12">
          <div className="card flex flex-col gap-4 p-6">
            <h1 className="text-2xl">Отчет недоступен</h1>
            <p className="subtle text-sm">
              Не удалось загрузить данные. Проверь API и корректность ID.
            </p>
            <a className="btn btn-secondary" href="/admin">
              Назад к дашборду
            </a>
          </div>
        </div>
      </main>
    );
  }
}
// #END_BLOCK_PAGE_RENDER
