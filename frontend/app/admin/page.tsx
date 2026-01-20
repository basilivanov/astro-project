// ############################################################################
// AI_HEADER: MODULE_ADMIN_DASHBOARD
// ROLE: Admin dashboard with client list.
// DEPENDENCIES: backend admin API, ClientForm.
// GRACE_ANCHORS: [ADMIN_PAGE]
// ############################################################################

import { revalidatePath } from "next/cache";
import Link from "next/link";
import { redirect } from "next/navigation";

import ClientForm from "../../components/client-form";

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

type AdminStats = {
  clients: number;
  reports_total: number;
  reports_in_progress: number;
  reports_completed: number;
  reports_failed: number;
};

const serverApiBase =
  process.env.INTERNAL_API_URL?.replace(/\/$/, "") ||
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://backend:8000";

async function fetchClients(): Promise<AdminClient[]> {
  const response = await fetch(`${serverApiBase}/api/admin/clients?limit=100`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Clients fetch failed: ${response.status}`);
  }
  return response.json();
}

async function fetchStats(): Promise<AdminStats> {
  const response = await fetch(`${serverApiBase}/api/admin/stats`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Stats fetch failed: ${response.status}`);
  }
  return response.json();
}

async function createClient(formData: FormData) {
  "use server";

  const readText = (key: string) => String(formData.get(key) || "").trim();
  const readNumber = (key: string) => {
    const raw = readText(key);
    if (!raw) return null;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  };

  const clientName = readText("client_name");
  const clientNote = readText("client_note");
  const birthDate = readText("birth_date");
  const birthLocation = readText("birth_location");
  const birthLat = readNumber("birth_lat");
  const birthLon = readNumber("birth_lon");
  const birthTimezone = readText("birth_timezone");
  const birthPlaceId = readText("birth_place_id");

  if (!clientName || !birthDate || !birthLocation) {
    redirect("/admin?error=Заполните обязательные поля");
  }

  const payload = {
    client_name: clientName,
    client_note: clientNote || null,
    birth_date: birthDate,
    birth_location: birthLocation,
    birth_lat: birthLat,
    birth_lon: birthLon,
    birth_timezone: birthTimezone || null,
    birth_place_id: birthPlaceId || null,
  };

  const response = await fetch(`${serverApiBase}/api/admin/clients`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let message = `Ошибка API: ${response.status}`;
    try {
      const data = await response.json();
      if (data?.detail) {
        message = String(data.detail);
      }
    } catch {
      // ignore
    }
    redirect(`/admin?error=${encodeURIComponent(message)}`);
  }

  const data = await response.json();
  revalidatePath("/admin");
  if (data?.id) {
    redirect(`/clients/${data.id}`);
  }
  redirect("/admin");
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

export default async function AdminPage({
  searchParams,
}: {
  searchParams?: { error?: string | string[] };
}) {
  const errorParam = searchParams?.error;
  const errorMessage = Array.isArray(errorParam) ? errorParam[0] : errorParam;

  let clients: AdminClient[] = [];
  let stats: AdminStats | null = null;
  try {
    clients = await fetchClients();
  } catch (err) {
    console.error(err);
  }
  try {
    stats = await fetchStats();
  } catch (err) {
    console.error(err);
  }

  return (
    <main className="page">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-5 py-8 sm:px-6 sm:py-12">
        <header className="flex flex-col gap-2">
          <div className="eyebrow">Astro-GRACE Admin</div>
          <h1 className="text-3xl font-bold sm:text-4xl">Клиенты</h1>
          <p className="subtle">Управление базой клиентов и генерация отчетов.</p>
        </header>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <div className="card p-4">
            <div className="label">Клиенты</div>
            <div className="text-2xl font-semibold">
              {stats?.clients ?? "—"}
            </div>
          </div>
          <div className="card p-4">
            <div className="label">Отчеты всего</div>
            <div className="text-2xl font-semibold">
              {stats?.reports_total ?? "—"}
            </div>
          </div>
          <div className="card p-4">
            <div className="label">В работе</div>
            <div className="text-2xl font-semibold">
              {stats?.reports_in_progress ?? "—"}
            </div>
          </div>
          <div className="card p-4">
            <div className="label">Готово</div>
            <div className="text-2xl font-semibold">
              {stats?.reports_completed ?? "—"}
            </div>
          </div>
          <div className="card p-4">
            <div className="label">Ошибки</div>
            <div className="text-2xl font-semibold">
              {stats?.reports_failed ?? "—"}
            </div>
          </div>
        </section>

        <div className="grid gap-8 lg:grid-cols-[350px_1fr]">
          <aside className="flex flex-col gap-6">
            <div className="card p-5">
              <h2 className="mb-4 text-xl font-semibold">Новый клиент</h2>
              <ClientForm action={createClient} errorMessage={errorMessage} />
            </div>
          </aside>

          <section className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Список ({clients.length})</h2>
            </div>

            {clients.length === 0 ? (
              <div className="card p-8 text-center subtle">
                Список пуст. Добавьте первого клиента.
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {clients.map((client) => (
                  <Link
                    key={client.id}
                    href={`/clients/${client.id}`}
                    className="card group flex flex-col justify-between gap-4 p-5 transition-colors hover:border-purple-500/50"
                  >
                    <div>
                      <h3 className="text-lg font-bold group-hover:text-purple-400">
                        {client.full_name}
                      </h3>
                      <p className="subtle text-xs mt-1">
                        {client.birth_location || "Без локации"} ·{" "}
                        {new Date(client.birth_datetime || "").getFullYear() || "?"}
                      </p>
                    </div>

                    <div className="flex items-end justify-between border-t border-white/5 pt-3">
                      <div>
                        <p className="text-xs font-medium text-white/70">
                          Отчетов: {client.report_count}
                        </p>
                        {client.last_report && (
                          <p className="text-[10px] subtle mt-0.5">
                            Последний:{" "}
                            {formatDateTime(client.last_report.created_at).split(" ")[0]}
                          </p>
                        )}
                      </div>
                      <span className="text-xs text-purple-400 opacity-0 transition-opacity group-hover:opacity-100">
                        Открыть →
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
