// ############################################################################
// AI_HEADER: MODULE_ADMIN_CLIENT_DETAIL
// ROLE: Admin client detail view and report generation.
// DEPENDENCIES: backend admin API, ReportForm.
// GRACE_ANCHORS: [DATA_FETCH, PAGE_RENDER]
// ############################################################################

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";

import ReportForm from "../../../../components/report-form";
import ClientForm from "../../../../components/client-form";

export const dynamic = "force-dynamic";

type AdminClient = {
  id: string;
  full_name: string;
  email?: string | null;
  notes?: string | null;
  birth_datetime?: string | null;
  birth_time_known: boolean;
  birth_location?: string | null;
  birth_lat?: number | null;
  birth_lon?: number | null;
  birth_timezone?: string | null;
  birth_place_id?: string | null;
  created_at: string;
  report_count: number;
};

type AdminReport = {
  id: string;
  report_type: string;
  status: string;
  paid: boolean;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  client_id: string;
  client_name: string;
  chunk_count: number;
};

type ClientDetail = {
  client: AdminClient;
  reports: AdminReport[];
};

const serverApiBase =
  process.env.INTERNAL_API_URL?.replace(/\/$/, "") ||
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://backend:8000";

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

async function fetchClientDetail(clientId: string): Promise<ClientDetail> {
  const response = await fetch(`${serverApiBase}/api/admin/clients/${clientId}`, {
    cache: "no-store",
    headers: { "X-Telegram-Auth": "123456789" }
  });
  if (!response.ok) {
    throw new Error(`Client fetch failed: ${response.status}`);
  }
  return response.json() as Promise<ClientDetail>;
}

async function createReportForClient(formData: FormData) {
  "use server";

  const readText = (key: string) => String(formData.get(key) || "").trim();
  const readNumber = (key: string) => {
    const raw = readText(key);
    if (!raw) return null;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  };

  const clientId = readText("client_id");
  const redirectClientId = clientId || "unknown";
  const clientName = readText("client_name");
  const clientNote = readText("client_note");
  
  const birthDateOnly = readText("birth_date_only");
  const birthTime = readText("birth_time");
  const birthTimeUnknown = formData.get("birth_time_unknown") === "on";
  
  let birthDate = readText("birth_date"); // Fallback for defaults/hidden
  if (birthDateOnly) {
      const timePart = birthTimeUnknown || !birthTime ? "12:00" : birthTime;
      birthDate = `${birthDateOnly}T${timePart}:00`;
  }

  const birthLocation = readText("birth_location");
  const reportType = readText("report_type") || "natal_master";
  const houseSystem = readText("house_system");
  const includeFixedStars = formData.get("include_fixed_stars") === "on";
  const fixedStarOrbRaw = readText("fixed_star_orb");
  const fixedStarOrb = Number(fixedStarOrbRaw || "1.0");
  const birthLat = readNumber("birth_lat");
  const birthLon = readNumber("birth_lon");
  const birthTimezone = readText("birth_timezone");
  const birthPlaceId = readText("birth_place_id");
  const question = readText("question");
  const partnerName = readText("partner_name");
  const partnerBirthDate = readText("partner_birth_date");
  const partnerBirthLocation = readText("partner_birth_location");
  const partnerBirthLat = readNumber("partner_birth_lat");
  const partnerBirthLon = readNumber("partner_birth_lon");
  const partnerBirthTimezone = readText("partner_birth_timezone");
  const partnerBirthPlaceId = readText("partner_birth_place_id");
  const solarCurrentLocationRaw = readText("solar_current_location");
  const solarCurrentLatRaw = readNumber("solar_current_lat");
  const solarCurrentLonRaw = readNumber("solar_current_lon");
  const solarCurrentTimezone = readText("solar_current_timezone");
  const solarCurrentPlaceId = readText("solar_current_place_id");
  const solarNextLocationRaw = readText("solar_next_location");
  const solarNextLatRaw = readNumber("solar_next_lat");
  const solarNextLonRaw = readNumber("solar_next_lon");
  const solarNextTimezone = readText("solar_next_timezone");
  const solarNextPlaceId = readText("solar_next_place_id");
  const solarCurrentLocation = solarCurrentLocationRaw || birthLocation;
  const solarCurrentLat = solarCurrentLatRaw ?? birthLat;
  const solarCurrentLon = solarCurrentLonRaw ?? birthLon;
  const solarNextLocation = solarNextLocationRaw || solarCurrentLocation || birthLocation;
  const solarNextLat = solarNextLatRaw ?? solarCurrentLat ?? birthLat;
  const solarNextLon = solarNextLonRaw ?? solarCurrentLon ?? birthLon;

  if (!clientName || !birthDate || !birthLocation) {
    redirect(`/clients/${redirectClientId}?error=Заполните обязательные поля`);
  }

  const payload = {
    client_id: clientId || null,
    client_name: clientName,
    client_note: clientNote || null,
    birth_date: birthDate,
    birth_time_known: !birthTimeUnknown,
    birth_location: birthLocation,
    birth_lat: birthLat,
    birth_lon: birthLon,
    birth_timezone: birthTimezone || null,
    birth_place_id: birthPlaceId || null,
    question: question || null,
    partner_name: partnerName || null,
    partner_birth_date: partnerBirthDate || null,
    partner_birth_location: partnerBirthLocation || null,
    partner_birth_lat: partnerBirthLat,
    partner_birth_lon: partnerBirthLon,
    partner_birth_timezone: partnerBirthTimezone || null,
    partner_birth_place_id: partnerBirthPlaceId || null,
    solar_current_location: solarCurrentLocation || null,
    solar_current_lat: solarCurrentLat,
    solar_current_lon: solarCurrentLon,
    solar_current_timezone: solarCurrentTimezone || null,
    solar_current_place_id: solarCurrentPlaceId || null,
    solar_next_location: solarNextLocation || null,
    solar_next_lat: solarNextLat,
    solar_next_lon: solarNextLon,
    solar_next_timezone: solarNextTimezone || null,
    solar_next_place_id: solarNextPlaceId || null,
    report_type: reportType,
    house_system: houseSystem || null,
    include_fixed_stars: includeFixedStars,
    fixed_star_orb: Number.isFinite(fixedStarOrb) ? fixedStarOrb : 1.0,
  };

  const response = await fetch(`${serverApiBase}/api/workflows/report/async`, {
    method: "POST",
    headers: { 
        "Content-Type": "application/json",
        "X-Telegram-Auth": "123456789"
    },
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
      // ignore parse errors, keep fallback message
    }
    redirect(`/clients/${redirectClientId}?error=${encodeURIComponent(message)}`);
  }

  const data = await response.json();
  if (data?.report_id) {
    redirect(`/reports/${data.report_id}`);
  }

  redirect(`/clients/${redirectClientId}?error=Отчет создан, но ID не найден.`);
}

async function updateClient(formData: FormData) {
  "use server";

  const readText = (key: string) => String(formData.get(key) || "").trim();
  const readNumber = (key: string) => {
    const raw = readText(key);
    if (!raw) return null;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  };

  const clientId = readText("client_id");
  const clientName = readText("client_name");
  const clientNote = readText("client_note");
  
  const birthDateOnly = readText("birth_date_only");
  const birthTime = readText("birth_time");
  const birthTimeUnknown = formData.get("birth_time_unknown") === "on";
  
  let birthDate = readText("birth_date"); 
  if (birthDateOnly) {
      const timePart = birthTimeUnknown || !birthTime ? "12:00" : birthTime;
      birthDate = `${birthDateOnly}T${timePart}:00`;
  }

  const birthLocation = readText("birth_location");
  const birthLat = readNumber("birth_lat");
  const birthLon = readNumber("birth_lon");
  const birthTimezone = readText("birth_timezone");
  const birthPlaceId = readText("birth_place_id");

  if (!clientName || !birthDate || !birthLocation) {
    redirect(`/clients/${clientId}?error=Заполните обязательные поля`);
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
  };

  const response = await fetch(`${serverApiBase}/api/admin/clients/${clientId}`, {
    method: "PUT",
    headers: { 
        "Content-Type": "application/json",
        "X-Telegram-Auth": "123456789"
    },
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
    redirect(`/clients/${clientId}?error=${encodeURIComponent(message)}`);
  }

  revalidatePath(`/clients/${clientId}`);
  redirect(`/clients/${clientId}`);
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
    const data = await fetchClientDetail(params.id);
    const client = data.client;

    return (
      <div className="page">
        <div className="mx-auto flex max-w-6xl flex-col gap-8 px-5 py-8 sm:px-6 sm:py-12">
          <header className="flex flex-col gap-3">
            <div className="eyebrow">Клиент</div>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <h1 className="text-2xl sm:text-3xl md:text-4xl">{client.full_name}</h1>
              <a className="btn btn-secondary" href="/admin">
                Назад к списку
              </a>
            </div>
            <p className="subtle text-sm">
              Дата рождения: {formatDateTime(client.birth_datetime)} ·{" "}
              {client.birth_location || "Локация не указана"}
            </p>
            {client.notes ? (
              <p className="subtle text-sm">Комментарий: {client.notes}</p>
            ) : null}
          </header>

          <details className="accordion">
            <summary className="accordion__summary cursor-pointer select-none">
                <span className="text-sm font-medium text-purple-400 hover:text-purple-300 transition-colors">
                    Редактировать профиль
                </span>
            </summary>
            <div className="pt-4">
                <ClientForm 
                    action={updateClient} 
                    errorMessage={errorMessage}
                    clientId={client.id}
                    defaults={{
                        name: client.full_name,
                        note: client.notes,
                        birthDate: client.birth_datetime || "",
                        birthTimeKnown: client.birth_time_known,
                        birthLocation: client.birth_location || "",
                        birthLat: client.birth_lat ?? null,
                        birthLon: client.birth_lon ?? null,
                        birthTimezone: client.birth_timezone ?? null,
                        birthPlaceId: client.birth_place_id ?? null,
                    }}
                />
            </div>
          </details>

          <section className="grid gap-8 lg:grid-cols-[1.3fr_0.7fr]">
            <ReportForm
              action={createReportForClient}
              errorMessage={errorMessage}
              hideClientFields
              clientId={client.id}
              clientDefaults={{
                name: client.full_name,
                note: client.notes,
                birthDate: client.birth_datetime || "",
                birthTimeKnown: client.birth_time_known,
                birthLocation: client.birth_location || "",
                birthLat: client.birth_lat ?? null,
                birthLon: client.birth_lon ?? null,
                birthTimezone: client.birth_timezone ?? null,
                birthPlaceId: client.birth_place_id ?? null,
              }}
            />

            <div className="card reveal flex flex-col gap-4 p-6" style={{ animationDelay: "0.3s" }}>
              <h3 className="text-xl">Отчеты клиента</h3>
              {data.reports.length === 0 ? (
                <p className="subtle text-sm">Отчетов пока нет.</p>
              ) : (
                <div className="flex flex-col gap-3">
                  {data.reports.map((report) => (
                    <div key={report.id} className="flex items-center justify-between gap-4 p-3 rounded-lg border border-slate-800 bg-slate-900/50">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                            <p className="text-sm font-bold">{formatReportType(report.report_type)}</p>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-bold ${
                                report.status === 'completed' ? 'bg-green-900/30 text-green-400' :
                                report.status === 'failed' ? 'bg-rose-900/30 text-rose-400' :
                                'bg-amber-900/30 text-amber-400'
                            }`}>
                                {report.status}
                            </span>
                        </div>
                        <p className="subtle text-[10px] uppercase tracking-wider">{formatDateTime(report.created_at)}</p>
                        {report.status === 'failed' && report.error_message && (
                            <p className="text-rose-400 text-[10px] mt-1 italic break-all">
                                {report.error_message}
                            </p>
                        )}
                      </div>
                      <a className="btn btn-secondary btn-sm px-3 py-1 text-xs" href={`/reports/${report.id}`}>
                        Открыть
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    );
  } catch {
    return (
      <div className="page">
        <div className="mx-auto flex max-w-3xl flex-col gap-6 px-5 py-8 sm:px-6 sm:py-12">
          <div className="card flex flex-col gap-4 p-6">
            <h1 className="text-2xl">Клиент не найден</h1>
            <p className="subtle text-sm">Проверь ID клиента и доступность API.</p>
            <a className="btn btn-secondary" href="/">
              Назад к списку
            </a>
          </div>
        </div>
      </div>
    );
  }
}
