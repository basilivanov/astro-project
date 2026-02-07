import Link from "next/link";
import { 
  Users, 
  FileText, 
  Activity, 
  CheckCircle2, 
  AlertCircle 
} from "lucide-react";

export const dynamic = "force-dynamic";

type AdminStats = {
  clients: number;
  reports_total: number;
  reports_in_progress: number;
  reports_completed: number;
  reports_failed: number;
  reports_by_type?: Record<string, number>;
  reports_daily?: { date: string; count: number }[];
  tasks_open?: number;
  tasks_total?: number;
  analytics_funnel?: Record<string, number>;
  window_days?: number;
  feedback_avg?: number;
  feedback_count?: number;
};

type AdminFeedback = {
  id: string;
  report_id: string;
  rating: number;
  comment?: string;
  created_at: string;
  report_type: string;
  client_name: string;
};

type AdminReport = {
  id: string;
  report_type: string;
  status: string;
  created_at: string;
  client_name: string;
};

const serverApiBase =
  process.env.INTERNAL_API_URL?.replace(/\/$/, "") ||
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://backend:8000";

async function fetchStats(windowDays: number, showTest?: boolean): Promise<AdminStats> {
  const url = new URL(`${serverApiBase}/api/admin/stats`);
  url.searchParams.set("days", String(windowDays));
  if (showTest) url.searchParams.set("show_test", "true");
  const response = await fetch(url.toString(), {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Stats fetch failed: ${response.status}`);
  }
  return response.json();
}

async function fetchFeedback(): Promise<AdminFeedback[]> {
  const url = new URL(`${serverApiBase}/api/admin/feedback`);
  url.searchParams.set("limit", "10");
  const response = await fetch(url.toString(), { cache: "no-store" });
  if (!response.ok) return [];
  return response.json();
}

async function fetchRecentReports(showTest?: boolean): Promise<AdminReport[]> {
  const url = new URL(`${serverApiBase}/api/admin/reports`);
  url.searchParams.set("limit", "10");
  if (showTest) url.searchParams.set("show_test", "true");
  const response = await fetch(url.toString(), {
    cache: "no-store",
  });
  if (!response.ok) {
    return [];
  }
  return response.json();
}

const parseWindowDays = (value?: string | string[]) => {
  const raw = Array.isArray(value) ? value[0] : value;
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) return 7;
  return Math.min(30, Math.max(1, Math.floor(parsed)));
};

const buildAdminLink = (days: number, showTest?: boolean) => {
  const params = new URLSearchParams();
  params.set("days", String(days));
  if (showTest) params.set("show_test", "true");
  return `/admin/dashboard?${params.toString()}`;
};

const formatReportType = (value?: string) =>
  value ? value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase()) : "—";

const formatDateTime = (value?: string | null) => {
  if (!value) return "—";
  try {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat("ru-RU", {
      dateStyle: "short",
      timeStyle: "short",
    }).format(date);
  } catch (e) {
    return value || "—";
  }
};

const getStatusColor = (status: string) => {
    switch (status) {
        case 'completed': return 'text-green-600 bg-green-50';
        case 'in_progress': return 'text-amber-600 bg-amber-50';
        case 'failed': return 'text-rose-600 bg-rose-50';
        default: return 'text-slate-500 bg-slate-50';
    }
}

// #START_BLOCK_ADMIN_DASHBOARD
/**
 * PURPOSE: Main admin dashboard page showing stats, funnel, and recent activity.
 * INPUT: searchParams (days, show_test).
 * OUTPUT: JSX Element (Server Component).
 * CONTEXT: Fetches data from internal API.
 */
export default async function DashboardPage({
  searchParams,
}: {
  searchParams?: { [key: string]: string | string[] | undefined };
}) {
  const windowDays = parseWindowDays(searchParams?.days);
  const showTest = searchParams?.show_test === "true";
  
  let stats: AdminStats | null = null;
  let recentReports: AdminReport[] = [];
  let recentFeedback: AdminFeedback[] = [];
  
  try {
    stats = await fetchStats(windowDays, showTest);
  } catch (err) {
    console.error("fetchStats error:", err);
  }
  try {
    recentReports = await fetchRecentReports(showTest);
  } catch (err) {
    console.error("fetchRecentReports error:", err);
  }
  try {
    recentFeedback = await fetchFeedback();
  } catch (err) {
    console.error("fetchFeedback error:", err);
  }

  const daily = stats?.reports_daily ?? [];
  const maxDaily = Math.max(...daily.map((item) => item.count || 0), 1);
  const weeklyTotal = daily.reduce((sum, item) => sum + (item.count || 0), 0);

  const funnelOrder = [
      { key: "landing_view", label: "Просмотр лендинга" },
      { key: "login_completed", label: "Вход в приложение" },
      { key: "report_generation_started", label: "Старт отчета" },
      { key: "checkout_started", label: "Клик оплаты" },
      { key: "payment_succeeded", label: "Успешная оплата" }
  ];
  
  const funnelData = stats?.analytics_funnel || {};
  const maxFunnel = (funnelData["landing_view"] as number) || 1;

  return (
    <div className="flex flex-col gap-8 py-8">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-slate-900">Дашборд</h1>
        <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-500">Окно статистики:</span>
            <div className="flex bg-white rounded-lg border border-slate-200 p-1">
                {[7, 14, 30].map((days) => (
                <Link
                    key={days}
                    href={buildAdminLink(days, showTest)}
                    className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${
                    windowDays === days
                        ? "bg-purple-100 text-purple-700 shadow-sm"
                        : "text-slate-500 hover:text-slate-700"
                    }`}
                >
                    {days} дней
                </Link>
                ))}
            </div>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <div className="glass-card p-5 bg-white flex flex-col justify-between h-32">
            <div className="flex justify-between items-start">
                <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Клиенты</span>
                <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                    <Users size={20} />
                </div>
            </div>
            <div className="text-3xl font-black text-slate-900">{stats?.clients ?? "—"}</div>
        </div>
        
        <div className="glass-card p-5 bg-white flex flex-col justify-between h-32">
            <div className="flex justify-between items-start">
                <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Отчеты</span>
                <div className="p-2 bg-purple-50 text-purple-600 rounded-lg">
                    <FileText size={20} />
                </div>
            </div>
            <div className="text-3xl font-black text-slate-900">{stats?.reports_total ?? "—"}</div>
        </div>

        <div className="glass-card p-5 bg-white flex flex-col justify-between h-32">
            <div className="flex justify-between items-start">
                <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">В работе</span>
                <div className="p-2 bg-amber-50 text-amber-600 rounded-lg">
                    <Activity size={20} />
                </div>
            </div>
            <div className="text-3xl font-black text-amber-600">{stats?.reports_in_progress ?? "—"}</div>
        </div>

        <div className="glass-card p-5 bg-white flex flex-col justify-between h-32">
            <div className="flex justify-between items-start">
                <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Ошибки</span>
                <div className="p-2 bg-rose-50 text-rose-600 rounded-lg">
                    <AlertCircle size={20} />
                </div>
            </div>
            <div className="text-3xl font-black text-rose-600">{stats?.reports_failed ?? "—"}</div>
        </div>

        <div className="glass-card p-5 bg-white flex flex-col justify-between h-32">
            <div className="flex justify-between items-start">
                <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Рейтинг</span>
                <div className="p-2 bg-amber-50 text-amber-500 rounded-lg">
                    <CheckCircle2 size={20} />
                </div>
            </div>
            <div>
                <div className="text-3xl font-black text-slate-900">{stats?.feedback_avg?.toFixed(1) || "0.0"}</div>
                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wide">отзывов: {stats?.feedback_count ?? 0}</div>
            </div>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[2fr_1fr]">
        
        {/* Funnel & Charts Column */}
        <div className="flex flex-col gap-8">
            {/* Funnel */}
            <div className="glass-card p-6 bg-white shadow-sm border border-slate-100">
                <h3 className="font-bold text-slate-800 mb-6 flex items-center gap-2">
                    <Activity size={18} className="text-purple-500" />
                    Воронка конверсии
                </h3>
                <div className="space-y-3">
                    {funnelOrder.map((step, idx) => {
                        const val = (funnelData[step.key] as number) || 0;
                        const prevVal = idx > 0 ? ((funnelData[funnelOrder[idx-1].key] as number) || 1) : val;
                        const conversion = idx > 0 ? Math.round((val / prevVal) * 100) : 100;
                        const width = Math.max(5, Math.round((val / maxFunnel) * 100));
                        
                        return (
                            <div key={step.key} className="relative">
                                <div className="flex justify-between text-xs font-bold text-slate-500 mb-1 uppercase tracking-wide">
                                    <span>{step.label}</span>
                                    <span>{val} {idx > 0 && <span className="text-slate-400 font-normal">({conversion}%)</span>}</span>
                                </div>
                                <div className="h-8 bg-slate-50 rounded-lg overflow-hidden relative">
                                    <div 
                                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500 opacity-80"
                                        style={{ width: `${width}%` }}
                                    ></div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Charts */}
            <div className="glass-card p-6 bg-white shadow-sm border border-slate-100">
                <div className="font-bold text-slate-800 mb-6 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <FileText size={18} className="text-blue-500" />
                        <span>Динамика отчетов</span>
                    </div>
                    <span className="text-xs font-normal text-slate-400 bg-slate-50 px-2 py-1 rounded">Всего за период: {weeklyTotal}</span>
                </div>
                
                {daily.length === 0 ? (
                <div className="text-center text-slate-400 text-sm py-10">Нет данных</div>
                ) : (
                <div>
                    <div className="flex h-40 items-end gap-2">
                    {daily.map((item) => {
                        const height = Math.max(5, Math.round(((item.count || 0) / maxDaily) * 100));
                        return (
                        <div
                            key={item.date}
                            className="flex-1 group relative"
                        >
                            <div 
                                className="w-full rounded-t-md bg-purple-500/80 hover:bg-purple-600 transition-colors"
                                style={{ height: `${height}%` }}
                            ></div>
                            <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-[10px] px-2 py-1 rounded whitespace-nowrap pointer-events-none transition-opacity z-10 shadow-lg">
                                {item.count} шт.
                            </div>
                        </div>
                        );
                    })}
                    </div>
                    <div className="mt-2 flex justify-between text-[10px] text-slate-400 font-medium px-1">
                        <span>{daily[0]?.date ? new Date(daily[0].date).toLocaleDateString("ru-RU") : ""}</span>
                        <span>{daily.length > 1 ? new Date(daily[daily.length - 1].date).toLocaleDateString("ru-RU") : ""}</span>
                    </div>
                </div>
                )}
            </div>

            {/* Feedback List */}
            <div className="glass-card p-6 bg-white shadow-sm border border-slate-100">
                <h3 className="font-bold text-slate-800 mb-6 flex items-center gap-2">
                    <CheckCircle2 size={18} className="text-amber-500" />
                    Свежие отзывы
                </h3>
                <div className="space-y-4">
                    {recentFeedback.length === 0 ? (
                        <p className="text-slate-400 text-sm py-10 text-center border border-dashed border-slate-100 rounded-xl">Пока нет отзывов.</p>
                    ) : (
                        recentFeedback.map(f => (
                            <div key={f.id} className="p-4 rounded-2xl bg-slate-50/50 border border-slate-100">
                                <div className="flex justify-between items-start mb-2">
                                    <div className="flex gap-1">
                                        {[1,2,3,4,5].map(s => (
                                            <span key={s} className={`text-xs ${s <= f.rating ? 'text-amber-400' : 'text-slate-200'}`}>★</span>
                                        ))}
                                    </div>
                                    <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">{formatDateTime(f.created_at)}</span>
                                </div>
                                <div className="text-xs font-bold text-slate-700 mb-1">{f.client_name} · {formatReportType(f.report_type)}</div>
                                {f.comment && <div className="text-sm text-slate-600 italic">«{f.comment}»</div>}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>

        {/* Recent Events Column */}
        <div className="flex flex-col gap-8">
            <div className="glass-card p-6 bg-white shadow-sm border border-slate-100 flex flex-col h-full min-h-[600px]">
                <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                    <Users size={18} className="text-slate-400" />
                    Последние события
                </h3>
                <div className="flex-1 overflow-y-auto pr-2 space-y-3">
                    {recentReports.length === 0 ? (
                        <p className="text-slate-400 text-sm">Нет событий.</p>
                    ) : (
                        recentReports.map(report => (
                            <Link 
                                key={report.id} 
                                href={`/admin/reports?id=${report.id}`} 
                                className="block p-3 rounded-xl border border-slate-100 hover:border-purple-200 hover:bg-purple-50/30 transition-all group"
                            >
                                <div className="flex justify-between items-start mb-1">
                                    <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${getStatusColor(report.status)}`}>
                                        {report.status}
                                    </span>
                                    <span className="text-[10px] text-slate-400">{formatDateTime(report.created_at)}</span>
                                </div>
                                <div className="text-sm font-bold text-slate-800 group-hover:text-purple-700 transition-colors truncate">
                                    {formatReportType(report.report_type)}
                                </div>
                                <div className="text-xs text-slate-500 truncate">
                                    {report.client_name}
                                </div>
                            </Link>
                        ))
                    )}
                </div>
                <div className="pt-4 mt-auto border-t border-slate-100 text-center">
                    <Link href="/admin/reports" className="text-xs font-bold text-purple-600 hover:text-purple-700 hover:underline">
                        Все отчеты →
                    </Link>
                </div>
            </div>
        </div>

      </div>
    </div>
  );
}
// #END_BLOCK_ADMIN_DASHBOARD
