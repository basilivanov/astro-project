"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { FileText, Calendar, User, Eye, RefreshCw } from "lucide-react";
import { RegenerateReportButton } from "../../../components/admin/RegenerateReportButton";
import { useTelegram } from "../../../hooks/useTelegram";
import { useSearchParams } from "next/navigation";

export const dynamic = "force-dynamic";

type AdminReport = {
  id: string;
  report_type: string;
  status: string;
  paid: boolean;
  created_at: string;
  updated_at: string;
  client_id: string;
  client_name: string;
  chunk_count: number;
};

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

const getStatusBadge = (status: string) => {
    const base = "px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border";
    switch (status) {
        case 'completed': return `${base} bg-green-50 text-green-700 border-green-200`;
        case 'in_progress': return `${base} bg-amber-50 text-amber-700 border-amber-200`;
        case 'failed': return `${base} bg-rose-50 text-rose-700 border-rose-200`;
        default: return `${base} bg-slate-50 text-slate-500 border-slate-200`;
    }
}

function ReportsPageContent() {
  const { initData, isReady } = useTelegram();
  const searchParams = useSearchParams();
  const status = searchParams.get("status");
  const showTest = searchParams.get("show_test") === "true";
  
  const [reports, setReports] = useState<AdminReport[]>([]);
  const [loading, setLoading] = useState(true);

  const fallbackReports: AdminReport[] = [];

  useEffect(() => {
    if (!isReady) return;
    
    const fetchReports = async () => {
      setLoading(true);
      try {
        const url = new URL("/api/admin/reports", window.location.origin);
        url.searchParams.set("limit", "100");
        if (status) url.searchParams.set("status", status);
        if (showTest) url.searchParams.set("show_test", "true");
        
        const response = await fetch(url.toString(), {
          headers: { "X-Telegram-Auth": initData }
        });
        if (response.ok) {
          const data = await response.json();
          setReports(Array.isArray(data) ? data : fallbackReports);
        } else {
          setReports(fallbackReports);
        }
      } catch (err) {
        console.error(err);
        setReports(fallbackReports);
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, [isReady, initData, status, showTest]);

  return (
    <div className="flex flex-col gap-6 py-6 pb-24" data-testid="admin-reports-page">
      <div className="flex flex-col gap-4">
        <div className="flex justify-between items-center px-1">
            <h1 className="text-2xl font-black text-slate-900">Отчеты</h1>
            <span className="bg-slate-100 text-slate-500 text-xs font-bold px-2 py-1 rounded-lg">{reports.length}</span>
        </div>
        
        <div className="overflow-x-auto -mx-4 px-4 pb-2 hide-scrollbar">
            <div className="flex gap-2">
                {['', 'completed', 'in_progress', 'failed'].map((s) => (
                <Link
                    key={s}
                    href={`/admin/reports${s ? `?status=${s}` : ''}${showTest ? (s ? '&' : '?') + 'show_test=true' : ''}`}
                    className={`whitespace-nowrap px-4 py-2 text-xs font-bold rounded-xl transition-all border ${
                    (status === s || (!status && !s))
                        ? "bg-purple-600 text-white border-purple-600 shadow-lg shadow-purple-200"
                        : "bg-white text-slate-500 border-slate-200 hover:border-slate-300"
                    }`}
                >
                    {s ? s.replace('_', ' ').toUpperCase() : 'ВСЕ'}
                </Link>
                ))}
            </div>
        </div>
      </div>

      {loading ? (
          <div className="text-center py-20 text-slate-400" data-testid="admin-reports-loading">Загрузка...</div>
      ) : (
        <>
          {/* Mobile Cards */}
          <div className="grid gap-3 md:hidden" data-testid="admin-reports-queue-mobile">
            {reports.length === 0 ? (
                <div className="hidden rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-slate-400 md:hidden" data-testid="admin-report-empty-card-mobile">Нет отчетов</div>
            ) : (
                reports.map((report) => (
                    <Link 
                        key={report.id} 
                        data-testid="admin-report-link" href={`/admin/reports/${report.id}`}
                        className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm active:scale-[0.98] transition-all flex flex-col gap-3"
                    >
                        <div className="flex justify-between items-start">
                            <div className="flex items-center gap-2">
                                <span className={getStatusBadge(report.status)}>{report.status}</span>
                                {report.paid && <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">PAID</span>}
                            </div>
                            <span className="text-[10px] text-slate-400 font-medium">{formatDateTime(report.created_at)}</span>
                        </div>
                        
                        <div>
                            <h3 className="font-bold text-slate-800 text-sm mb-1">{formatReportType(report.report_type)}</h3>
                            <div className="flex items-center gap-2 text-xs text-slate-500">
                                <User size={12} />
                                {report.client_name}
                            </div>
                        </div>
                        
                        <div className="pt-3 border-t border-slate-50 flex justify-between items-center mt-1">
                            <span className="text-[10px] text-slate-400">ID: ...{report.id.slice(-6)}</span>
                            <div className="flex items-center gap-1 text-purple-600 font-bold text-xs">
                                Открыть <Eye size={14} />
                            </div>
                        </div>
                    </Link>
                ))
            )}
          </div>

          {/* Desktop Table */}
          <div className="hidden md:block glass-card bg-white overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="bg-slate-50 text-slate-500 font-bold uppercase text-xs border-b border-slate-100">
                        <tr>
                            <th className="px-6 py-4">Клиент</th>
                            <th className="px-6 py-4">Тип</th>
                            <th className="px-6 py-4">Статус</th>
                            <th className="px-6 py-4">Дата</th>
                            <th className="px-6 py-4 text-right">Действия</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50" data-testid="admin-reports-queue">{reports.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-slate-400" data-testid="admin-report-empty-card">
                                    Отчетов не найдено.
                                </td>
                            </tr>
                        ) : (
                            reports.map((report) => (
                                <tr key={report.id} className="hover:bg-purple-50/30 transition-colors group cursor-pointer">
                                    <td className="px-6 py-4 font-medium text-slate-900">
                                        <div className="flex items-center gap-2">
                                            <User size={16} className="text-slate-400" />
                                            {report.client_name}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-slate-600">
                                        <div className="flex items-center gap-2">
                                            <FileText size={16} className="text-slate-400" />
                                            {formatReportType(report.report_type)}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={getStatusBadge(report.status)}>{report.status}</span>
                                    </td>
                                    <td className="px-6 py-4 text-slate-500">
                                        <div className="flex items-center gap-2">
                                            <Calendar size={16} className="text-slate-400" />
                                            {formatDateTime(report.created_at)}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-right flex justify-end items-center gap-2">
                                        <RegenerateReportButton reportId={report.id} />
                                        <Link 
                                            data-testid="admin-report-link" href={`/admin/reports/${report.id}`} 
                                            className="inline-flex items-center gap-1 text-xs font-bold text-purple-600 hover:text-purple-800 bg-purple-50 hover:bg-purple-100 px-3 py-1.5 rounded-lg transition-colors"
                                        >
                                            <Eye size={14} />
                                            Открыть
                                        </Link>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function ReportsPage() {
  return (
    <Suspense fallback={<div className="p-6 text-sm text-slate-500">Загрузка...</div>}>
      <ReportsPageContent />
    </Suspense>
  );
}
