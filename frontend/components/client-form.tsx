// ############################################################################
// AI_HEADER: MODULE_CLIENT_FORM
// ROLE: Client creation form without report generation.
// DEPENDENCIES: GeoField.
// GRACE_ANCHORS: [CLIENT_FORM]
// ############################################################################

"use client";

import GeoField from "./geo-field";

type ClientFormProps = {
  action: (formData: FormData) => void | Promise<void>;
  errorMessage?: string | null;
};

export default function ClientForm({ action, errorMessage }: ClientFormProps) {
  return (
    <div className="card reveal flex flex-col gap-6 p-6" style={{ animationDelay: "0.15s" }}>
      <div className="flex items-center justify-between">
        <h2 className="text-2xl">Создать клиента</h2>
        <span className="badge badge--ok">Без отчета</span>
      </div>
      {errorMessage ? (
        <div className="text-sm text-[var(--accent-3)]">{errorMessage}</div>
      ) : null}
      <form action={action} className="grid gap-4">
        <div className="field">
          <label className="label" htmlFor="client_name_only">Имя клиента</label>
          <input
            id="client_name_only"
            name="client_name"
            className="input"
            placeholder="Иван Иванов"
            required
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
          />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="field">
            <label className="label" htmlFor="birth_date_only">Дата и время рождения</label>
            <input
              id="birth_date_only"
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
        <button className="btn btn-primary w-full justify-center" type="submit">
          Сохранить клиента
        </button>
      </form>
    </div>
  );
}
