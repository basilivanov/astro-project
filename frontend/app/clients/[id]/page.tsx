// ############################################################################
// AI_HEADER: MODULE_ADMIN_CLIENT_DETAIL
// ROLE: Admin client detail view and report generation.
// DEPENDENCIES: backend admin API, ReportForm.
// GRACE_ANCHORS: [DATA_FETCH, PAGE_RENDER]
// ############################################################################

import { redirect } from "next/navigation";

import ReportForm from "../../../components/report-form";

export const dynamic = "force-dynamic";

type AdminClient = {
  id: string;
  full_name: string;
  email?: string | null;
  notes?: string | null;
  birth_datetime?: string | null;
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
  const birthDate = readText("birth_date");
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
      <main className="page">
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
                    <div key={report.id} className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-sm">{formatReportType(report.report_type)}</p>
                        <p className="subtle text-xs">{formatDateTime(report.created_at)}</p>
                      </div>
                      <a className="btn btn-secondary" href={`/reports/${report.id}`}>
                        Открыть
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        </div>
      </main>
    );
  } catch {
    return (
      <main className="page">
        <div className="mx-auto flex max-w-3xl flex-col gap-6 px-5 py-8 sm:px-6 sm:py-12">
          <div className="card flex flex-col gap-4 p-6">
            <h1 className="text-2xl">Клиент не найден</h1>
            <p className="subtle text-sm">Проверь ID клиента и доступность API.</p>
            <a className="btn btn-secondary" href="/">
              Назад к списку
            </a>
          </div>
        </div>
      </main>
    );
  }
}
