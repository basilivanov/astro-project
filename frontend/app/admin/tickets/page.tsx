export const dynamic = "force-dynamic";

type AdminTicket = {
  id: string;
  user_id: string;
  username?: string | null;
  topic: string;
  status: string;
  message: string;
  created_at: string;
};

const serverApiBase =
  process.env.INTERNAL_API_URL?.replace(/\/$/, "") ||
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://backend:8000";

async function fetchTickets(): Promise<AdminTicket[]> {
  const response = await fetch(`${serverApiBase}/api/admin/tickets?limit=50`, {
    cache: "no-store",
  });
  if (!response.ok) {
    return [];
  }
  return response.json();
}

const formatDateTime = (value?: string | null) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
};

const ticketStatusBadge = (status: string) => {
    const base = "px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border";
    switch (status) {
        case "open": return `${base} bg-blue-50 text-blue-700 border-blue-200`;
        case "closed": return `${base} bg-slate-100 text-slate-500 border-slate-200`;
        default: return `${base} bg-slate-100 text-slate-500 border-slate-200`;
    }
}

export default async function TicketsPage() {
  let tickets: AdminTicket[] = [];
  try {
    tickets = await fetchTickets();
  } catch (err) {
    console.error(err);
  }

  return (
    <div className="flex flex-col gap-8 py-8">
      <header>
        <h1 className="text-3xl font-bold text-slate-900">Тикеты поддержки</h1>
        <p className="text-slate-500 font-medium">Обращения пользователей ({tickets.length})</p>
      </header>

      <section>
        {tickets.length === 0 ? (
          <div className="glass-card p-12 text-center text-slate-400">
            Нет активных обращений.
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {tickets.map((t) => (
              <div key={t.id} className="glass-card p-5 flex flex-col gap-3 bg-white">
                <div className="flex justify-between items-start">
                    <div className="flex items-center gap-2">
                        <span className={ticketStatusBadge(t.status)}>{t.status}</span>
                        <span className="text-xs font-bold text-purple-600 uppercase tracking-wider bg-purple-50 px-2 py-0.5 rounded-md">
                            {t.topic}
                        </span>
                    </div>
                    <span className="text-[10px] text-slate-400 font-medium">{formatDateTime(t.created_at)}</span>
                </div>
                
                <div className="flex items-center gap-2 text-sm text-slate-900 font-medium">
                    <span>User: {t.username ? `@${t.username}` : t.user_id.slice(0, 8)}</span>
                </div>

                <div className="bg-slate-50 p-4 rounded-xl text-sm text-slate-700 leading-relaxed border border-slate-100">
                    {t.message}
                </div>
                
                <div className="flex justify-end gap-2 mt-2">
                    {t.username && (
                        <a 
                            href={`https://t.me/${t.username}`} 
                            target="_blank" 
                            className="text-xs font-bold text-white bg-blue-500 hover:bg-blue-600 px-4 py-2 rounded-lg transition-colors"
                        >
                            Ответить в Telegram
                        </a>
                    )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
