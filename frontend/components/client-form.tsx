// ############################################################################
// AI_HEADER: MODULE_CLIENT_FORM
// ROLE: Client creation form without report generation.
// DEPENDENCIES: GeoField.
// GRACE_ANCHORS: [CLIENT_FORM]
// ############################################################################

"use client";

import { useState } from "react";
import GeoField from "./geo-field";

type ClientFormProps = {
  action: (formData: FormData) => void | Promise<void>;
  errorMessage?: string | null;
  clientId?: string;
  defaults?: {
    name: string;
    note?: string | null;
    userId?: string | null;
    birthDate: string; // ISO string
    birthTimeKnown?: boolean;
    birthLocation: string;
    birthLat?: number | null;
    birthLon?: number | null;
    birthTimezone?: string | null;
    birthPlaceId?: string | null;
  };
};

export default function ClientForm({ action, errorMessage, clientId, defaults }: ClientFormProps) {
  const [timeUnknown, setTimeUnknown] = useState(defaults?.birthTimeKnown === false);

  // Parse defaults
  const dateStr = defaults?.birthDate || "";
  let defaultDate = "";
  let defaultTime = "";
  if (dateStr.includes("T")) {
      [defaultDate, defaultTime] = dateStr.split("T");
      // Strip seconds if present
      if (defaultTime.length > 5) defaultTime = defaultTime.substring(0, 5);
  } else {
      defaultDate = dateStr;
  }

  return (
    <div className="card reveal flex flex-col gap-6 p-6" style={{ animationDelay: "0.15s" }}>
      <div className="flex items-center justify-between">
        <h2 className="text-2xl">{clientId ? "Редактировать клиента" : "Создать клиента"}</h2>
        <span className="badge badge--ok">{clientId ? "Правка" : "Новый"}</span>
      </div>
      {errorMessage ? (
        <div className="text-sm text-[var(--accent-3)]">{errorMessage}</div>
      ) : null}
      <form action={action} className="grid gap-4">
        {clientId && <input type="hidden" name="client_id" value={clientId} />}
        
        <div className="field">
          <label className="label" htmlFor="client_name_only">Имя клиента</label>
          <input
            id="client_name_only"
            name="client_name"
            className="input"
            placeholder="Иван Иванов"
            required
            defaultValue={defaults?.name}
          />
        </div>
        <div className="field">
          <label className="label" htmlFor="client_user_id">User ID (Optional)</label>
          <input
            id="client_user_id"
            name="user_id"
            className="input"
            placeholder="UUID пользователя"
            defaultValue={defaults?.userId}
          />
        </div>
        <div className="field">
          <label className="label" htmlFor="client_note_only">Комментарий</label>
          <textarea
            id="client_note_only"
            name="client_note"
            className="input textarea"
            placeholder="Короткая заметка о клиенте"
            rows={3}
            defaultValue={defaults?.note || ""}
          />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="field">
            <label className="label" htmlFor="cf_birth_date_only">Дата рождения</label>
            <input
              id="cf_birth_date_only"
              name="birth_date_only"
              type="date"
              className="input"
              required
              defaultValue={defaultDate}
            />
          </div>
          <div className="field">
            <div className="flex justify-between">
                <label className="label" htmlFor="cf_birth_time">Время</label>
                <label className="text-xs flex items-center gap-1 cursor-pointer">
                    <input 
                        type="checkbox" 
                        name="birth_time_unknown" 
                        checked={timeUnknown}
                        onChange={(e) => setTimeUnknown(e.target.checked)}
                    />
                    <span className="text-zinc-500">Неизвестно</span>
                </label>
            </div>
            {!timeUnknown && (
                <input
                  id="cf_birth_time"
                  name="birth_time"
                  type="time"
                  className="input animate-in fade-in duration-200"
                  defaultValue={defaultTime}
                />
            )}
          </div>
          <GeoField
            namePrefix="birth"
            label="Место рождения"
            placeholder="Начните вводить город"
            required
            initialLabel={defaults?.birthLocation}
            initialLat={defaults?.birthLat}
            initialLon={defaults?.birthLon}
            initialTimezone={defaults?.birthTimezone}
            initialPlaceId={defaults?.birthPlaceId}
          />
        </div>
        <button className="btn btn-primary w-full justify-center" type="submit">
          {clientId ? "Сохранить изменения" : "Создать клиента"}
        </button>
      </form>
    </div>
  );
}
