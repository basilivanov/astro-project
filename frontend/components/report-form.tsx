// ############################################################################
// AI_HEADER: MODULE_REPORT_FORM
// ROLE: Client-side report creation form with GeoNames autocomplete.
// DEPENDENCIES: /api/geo/autocomplete (Next proxy).
// GRACE_ANCHORS: [FORM_STATE, GEO_AUTOCOMPLETE]
// ############################################################################

"use client";

import { useState } from "react";

import GeoField from "./geo-field";

type ReportFormProps = {
  action: (formData: FormData) => void | Promise<void>;
  errorMessage?: string | null;
  hideClientFields?: boolean;
  clientId?: string;
  clientDefaults?: {
    name: string;
    note?: string | null;
    birthDate: string;
    birthLocation: string;
    birthLat?: number | null;
    birthLon?: number | null;
    birthTimezone?: string | null;
    birthPlaceId?: string | null;
  };
};

const PRODUCT_OPTIONS = [
  { value: "natal_master", label: "Натал (базовый)" },
  { value: "week_forecast", label: "Прогноз на неделю" },
  { value: "month_forecast", label: "Прогноз на месяц" },
  { value: "year_forecast", label: "Прогноз на год (по месяцам)" },
  { value: "ten_year_forecast", label: "Прогноз на 10 лет" },
  { value: "synastry", label: "Синастрия" },
  { value: "horary_answer", label: "Хорар" },
  { value: "custom", label: "Custom" },
];

const SOLAR_TYPES = new Set(["year_forecast", "ten_year_forecast"]);

export default function ReportForm({
  action,
  errorMessage,
  hideClientFields,
  clientId,
  clientDefaults,
}: ReportFormProps) {
  const [reportType, setReportType] = useState(PRODUCT_OPTIONS[0].value);
  const isSynastry = reportType === "synastry";
  const isHorary = reportType === "horary_answer";
  const needsSolar = SOLAR_TYPES.has(reportType);

  return (
    <div className="card reveal flex flex-col gap-6 p-6" style={{ animationDelay: "0.2s" }}>
      <div className="flex items-center justify-between">
        <h2 className="text-2xl">Создать отчет</h2>
        <span className="badge badge--warn">Ручной запуск</span>
      </div>
      {errorMessage ? (
        <div className="text-sm text-[var(--accent-3)]">{errorMessage}</div>
      ) : null}
      <form action={action} className="grid gap-4">
        {clientId ? <input type="hidden" name="client_id" value={clientId} /> : null}
        {hideClientFields && clientDefaults ? (
          <>
            <input type="hidden" name="client_name" value={clientDefaults.name} />
            <input type="hidden" name="client_note" value={clientDefaults.note || ""} />
            <input type="hidden" name="birth_date" value={clientDefaults.birthDate} />
            <input type="hidden" name="birth_location" value={clientDefaults.birthLocation} />
            <input type="hidden" name="birth_lat" value={clientDefaults.birthLat ?? ""} />
            <input type="hidden" name="birth_lon" value={clientDefaults.birthLon ?? ""} />
            <input type="hidden" name="birth_timezone" value={clientDefaults.birthTimezone || ""} />
            <input type="hidden" name="birth_place_id" value={clientDefaults.birthPlaceId || ""} />
          </>
        ) : (
          <>
            <div className="field">
              <label className="label" htmlFor="client_name">Имя клиента</label>
              <input
                id="client_name"
                name="client_name"
                className="input"
                placeholder="Иван Иванов"
                required
              />
            </div>
            <div className="field">
              <label className="label" htmlFor="client_note">Комментарий</label>
              <textarea
                id="client_note"
                name="client_note"
                className="input textarea"
                placeholder="Короткая заметка о клиенте"
                rows={3}
              />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="field">
                <label className="label" htmlFor="birth_date">Дата и время рождения</label>
                <input
                  id="birth_date"
                  name="birth_date"
                  type="datetime-local"
                  className="input"
                  required
                />
              </div>
              <GeoField
                namePrefix="birth"
                label="Место рождения"
                placeholder="Начните вводить город"
                required
              />
            </div>
          </>
        )}
        <div className="grid gap-4 md:grid-cols-2">
          <div className="field">
            <label className="label" htmlFor="report_type">Тип отчета</label>
            <select
              id="report_type"
              name="report_type"
              className="input"
              value={reportType}
              onChange={(event) => setReportType(event.target.value)}
            >
              {PRODUCT_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label className="label" htmlFor="house_system">Система домов (опц.)</label>
            <input
              id="house_system"
              name="house_system"
              className="input"
              placeholder="placidus"
            />
          </div>
        </div>
        {isHorary ? (
          <div className="field">
            <label className="label" htmlFor="question">
              Вопрос кверента
            </label>
            <textarea
              id="question"
              name="question"
              className="input textarea"
              placeholder="Введите хорарный вопрос..."
              rows={3}
              required={isHorary}
            />
          </div>
        ) : null}
        <div className="grid gap-4 md:grid-cols-2">
          <div className="field">
            <label className="label" htmlFor="fixed_star_orb">Орбис фикс. звезд</label>
            <input
              id="fixed_star_orb"
              name="fixed_star_orb"
              type="number"
              step="0.1"
              min="0"
              defaultValue="1.0"
              className="input"
            />
          </div>
          <label className="field checkbox">
            <span className="label">Фиксированные звезды</span>
            <input
              name="include_fixed_stars"
              type="checkbox"
              defaultChecked
            />
          </label>
        </div>

        {isSynastry ? (
          <div className="panel grid gap-4">
            <div className="panel-title">Данные партнера</div>
            <div className="field">
              <label className="label" htmlFor="partner_name">Имя партнера</label>
              <input
                id="partner_name"
                name="partner_name"
                className="input"
                placeholder="Партнер"
                required={isSynastry}
              />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="field">
                <label className="label" htmlFor="partner_birth_date">
                  Дата и время рождения партнера
                </label>
                <input
                  id="partner_birth_date"
                  name="partner_birth_date"
                  type="datetime-local"
                  className="input"
                  required={isSynastry}
                />
              </div>
              <GeoField
                namePrefix="partner_birth"
                label="Место рождения партнера"
                placeholder="Начните вводить город"
                required={isSynastry}
              />
            </div>
          </div>
        ) : null}

        {needsSolar ? (
          <div className="panel grid gap-4">
            <div className="panel-title">Солярные места</div>
            <div className="subtle text-sm">
              Если место не указано, будет использовано место рождения.
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <GeoField
                namePrefix="solar_current"
                label="Где был прошлый день рождения"
                placeholder="Город для текущего соляра"
              />
              <GeoField
                namePrefix="solar_next"
                label="Где будет следующий день рождения"
                placeholder="Город для следующего соляра"
              />
            </div>
          </div>
        ) : null}

        <button className="btn btn-primary w-full justify-center" type="submit">
          Сгенерировать отчет
        </button>
      </form>
    </div>
  );
}
