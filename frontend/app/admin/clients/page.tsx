"use client";

import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { User, Calendar, FileText, Search, Plus } from "lucide-react";
import ClientForm from "../../../components/client-form";
import AdminSearch from "../../../components/admin-search";
import { useTelegram } from "../../../hooks/useTelegram";
import { useSearchParams, useRouter } from "next/navigation";

export const dynamic = "force-dynamic";

type AdminClient = {
  id: string;
  full_name: string;
  email?: string | null;
  notes?: string | null;
  birth_datetime?: string | null;
  birth_location?: string | null;
  created_at: string;
  report_count: number;
  last_report?: {
    id: string;
    report_type: string;
    status: string;
    created_at: string;
  } | null;
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

export default function ClientsPage() {
  const { initData, isReady } = useTelegram();
  const searchParams = useSearchParams();
  const router = useRouter();
  const query = searchParams.get("q") || "";
  const showTest = searchParams.get("show_test") === "true";
  const errorParam = searchParams.get("error");

  const [clients, setClients] = useState<AdminClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchClients = async () => {
    if (!isReady) return;
    setLoading(true);
    try {
      const url = new URL("/api/admin/clients", window.location.origin);
      url.searchParams.set("limit", "100");
      if (query) url.searchParams.set("q", query);
      if (showTest) url.searchParams.set("show_test", "true");
      
      const response = await fetch(url.toString(), {
        headers: { "X-Telegram-Auth": initData }
      });
      if (response.ok) {
        const data = await response.json();
        setClients(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, [isReady, initData, query, showTest]);

  const handleCreateClient = async (formData: FormData) => {
    const readText = (key: string) => String(formData.get(key) || "").trim();
    const readNumber = (key: string) => {
      const raw = readText(key);
      if (!raw) return null;
      const parsed = Number(raw);
      return Number.isFinite(parsed) ? parsed : null;
    };

    const clientName = readText("client_name");
    const clientNote = readText("client_note");
    const birthDateOnly = readText("birth_date_only");
    const birthTimeUnknown = formData.get("birth_time_unknown") === "on";
    const birthTime = birthTimeUnknown ? "12:00" : (readText("birth_time") || "12:00");
    const birthDate = birthDateOnly ? `${birthDateOnly}T${birthTime}:00` : "";
    const birthLocation = readText("birth_location");
    const birthLat = readNumber("birth_lat");
    const birthLon = readNumber("birth_lon");
    const birthTimezone = readText("birth_timezone");
    const birthPlaceId = readText("birth_place_id");
    const userId = readText("user_id");

    if (!clientName || !birthDate || !birthLocation) {
      alert("Заполните обязательные поля");
      return;
    }

    const payload = {
      client_name: clientName,
      client_note: clientNote || null,
      birth_date: birthDate,
      birth_time_known: !birthTimeUnknown,
      birth_location: birthLocation,
      birth_lat: birthLat,
      birth_lon: birthLon,
      birth_timezone: birthTimezone || null,
      birth_place_id: birthPlaceId || null,
      user_id: userId || null,
    };

    setActionLoading(true);
    try {
      const response = await fetch("/api/admin/clients", {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "X-Telegram-Auth": initData
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data?.detail || `Ошибка API: ${response.status}`);
      }

      const data = await response.json();
      if (data?.id) {
        router.push(`/create?client_id=${data.id}`); // For B2C, usually go to report creation
      } else {
        fetchClients();
      }
    } catch (err: any) {
      alert(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 py-6 pb-24">
      <header className="flex flex-col gap-4">
        <div className="flex justify-between items-center px-1">
            <h1 className="text-2xl font-black text-slate-900">Клиенты</h1>
            <span className="bg-slate-100 text-slate-500 text-xs font-bold px-2 py-1 rounded-lg">{clients.length}</span>
        </div>
        <div className="w-full">
          <Suspense fallback={<div className="h-10 w-full bg-slate-100 rounded-xl animate-pulse" />}>
            <AdminSearch placeholder="Поиск клиента..." />
          </Suspense>
        </div>
      </header>

      <div className="grid gap-8 lg:grid-cols-[1fr_350px]">
        <section>
          {loading ? (
            <div className="text-center py-20 text-slate-400 font-medium">Загрузка...</div>
          ) : clients.length === 0 ? (
            <div className="bg-white p-12 text-center rounded-3xl border border-slate-100 shadow-sm flex flex-col items-center gap-4">
              <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center text-slate-300">
                <User size={32} />
              </div>
              <div>
                <div className="text-slate-900 mb-1 font-black text-xl">Список пуст</div>
                <p className="text-sm text-slate-500 max-w-xs mx-auto">
                  {query 
                    ? `По запросу "${query}" ничего не найдено. Попробуйте изменить параметры поиска.` 
                    : "У вас пока нет созданных клиентов. Создайте первого, чтобы начать работу."}
                </p>
              </div>
              {!query && (
                <button 
                  onClick={() => document.getElementById("client_name_only")?.focus()}
                  className="mt-2 px-6 py-3 bg-purple-600 text-white rounded-2xl font-bold text-sm hover:bg-purple-700 transition-colors shadow-lg shadow-purple-200"
                >
                  Создать клиента
                </button>
              )}
            </div>
          ) : (
            <div className="grid gap-3">
              {clients.map((client) => (
                <Link
                  key={client.id}
                  href={`/admin/clients/${client.id}`} 
                  className="bg-white group flex flex-col justify-between gap-4 p-5 rounded-2xl border border-slate-100 hover:border-purple-200 transition-all active:scale-[0.98] shadow-sm"
                >
                  <div className="flex justify-between items-start">
                    <div>
                        <h3 className="font-bold text-slate-800 group-hover:text-purple-600 transition-colors">
                        {client.full_name}
                        </h3>
                        <p className="text-slate-500 text-[10px] mt-0.5 font-bold uppercase tracking-wider">
                        {client.birth_location || "Без локации"} ·{" "}
                        {new Date(client.birth_datetime || "").getFullYear() || "?"}
                        </p>
                    </div>
                    <div className="bg-purple-50 text-purple-600 px-2 py-1 rounded-lg flex items-center gap-1">
                        <FileText size={12} />
                        <span className="text-xs font-black">{client.report_count}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between border-t border-slate-50 pt-3">
                    <span className="text-[10px] text-slate-400 font-mono">ID: ...{client.id.slice(-6)}</span>
                    <span className="text-xs text-purple-600 font-bold">
                      Открыть →
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>

        <aside className="flex flex-col gap-6">
          <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm sticky top-6">
            <h2 className="mb-4 text-xl font-black text-slate-900 flex items-center gap-2">
                <Plus size={20} className="text-purple-500" />
                Новый клиент
            </h2>
            <ClientForm action={handleCreateClient} errorMessage={errorParam} />
            {actionLoading && <div className="mt-4 text-center text-xs text-slate-400 animate-pulse">Сохранение...</div>}
          </div>
        </aside>
      </div>
    </div>
  );
}