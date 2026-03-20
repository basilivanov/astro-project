import { redirect } from "next/navigation";
import { Send, AlertTriangle, CheckCircle2 } from "lucide-react";

const serverApiBase =
  process.env.INTERNAL_API_URL?.replace(/\/$/, "") ||
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://backend:8000";

async function sendBroadcast(formData: FormData) {
  "use server";
  const text = String(formData.get("text") || "").trim();
  const imageUrl = String(formData.get("image_url") || "").trim();
  
  if (!text) return;

  await fetch(`${serverApiBase}/api/admin/broadcast`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
        text,
        image_url: imageUrl || null 
    }),
  });
  
  redirect("/admin/broadcast?success=true");
}

export default function BroadcastPage({
  searchParams,
}: {
  searchParams?: { success?: string };
}) {
  const success = searchParams?.success === "true";

  return (
    <div className="flex flex-col gap-8 py-8 max-w-2xl mx-auto">
      <header>
        <h1 className="text-3xl font-bold text-slate-900">Рассылка</h1>
        <p className="text-slate-500 font-medium">Отправка сообщений всем пользователям бота</p>
      </header>

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
            <CheckCircle2 size={20} />
            <div>
                <p className="font-bold">Рассылка запущена!</p>
                <p className="text-sm opacity-80">Сообщения отправляются в фоновом режиме.</p>
            </div>
        </div>
      )}

      <div className="glass-card p-8 bg-white">
        <form action={sendBroadcast} className="flex flex-col gap-6">
            <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 uppercase tracking-wider">Текст сообщения</label>
                <textarea 
                    name="text" 
                    placeholder="Привет! У нас новости..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 min-h-[160px] text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition-all resize-none"
                    required
                />
            </div>

            <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 uppercase tracking-wider">URL Картинки (опционально)</label>
                <input 
                    type="url"
                    name="image_url" 
                    placeholder="https://example.com/image.jpg"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition-all"
                />
            </div>

            <div className="bg-amber-50 border border-amber-100 rounded-xl p-4 flex gap-3 text-amber-800 text-sm">
                <AlertTriangle size={20} className="shrink-0" />
                <p>
                    Внимание! Сообщение будет отправлено <b>всем</b> пользователям, у которых есть диалог с ботом.
                    Рассылка идет пачками по 20 сообщений/сек.
                </p>
            </div>

            <button 
                type="submit" 
                className="gradient-primary py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2 hover:opacity-90 transition-opacity active:scale-[0.98]"
            >
                <Send size={20} />
                Отправить всем
            </button>
        </form>
      </div>
    </div>
  );
}
