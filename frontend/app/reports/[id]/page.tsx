// ############################################################################
// AI_HEADER: MODULE_ADMIN_REPORT_DETAIL
// ROLE: Admin report detail view.
// DEPENDENCIES: backend admin API.
// GRACE_ANCHORS: [TYPES, DATA_CONFIG, DATA_FETCH, PAGE_RENDER]
// ############################################################################

import { headers } from "next/headers";

import AdminReportDetailClient from "../../../components/admin/admin-report-detail-client";

export const dynamic = "force-dynamic";

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

const resolveApiBase = () => {
  const internal = process.env.INTERNAL_API_URL?.replace(/\/$/, "");
  if (internal) return internal;

  const publicBase = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (publicBase) return publicBase;

  const headerList = headers();
  const host = headerList.get("x-forwarded-host") || headerList.get("host");
  const proto = headerList.get("x-forwarded-proto") || "http";
  if (host) return `${proto}://${host}`;

  return "http://backend:8000";
};

async function fetchReportDetail(reportId: string): Promise<AdminReportDetail> {
  const response = await fetch(`${resolveApiBase()}/api/admin/reports/${reportId}?include_content=1`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`admin_report_fetch_failed_${response.status}`);
  }

  return response.json();
}

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
    const data = await fetchReportDetail(params.id);
    return <AdminReportDetailClient initialData={data} errorMessage={errorMessage} />;
  } catch {
    return (
      <div className="flex flex-col gap-6 py-8">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h1 className="text-2xl font-black text-slate-900">Отчёт недоступен</h1>
          <p className="mt-2 text-sm text-slate-500">Не удалось загрузить данные. Проверь API и корректность ID.</p>
          <a className="mt-4 inline-flex rounded-2xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" href="/admin/reports">Назад к списку</a>
        </div>
      </div>
    );
  }
}
