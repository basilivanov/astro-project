"use client";

import { useEffect, useState } from "react";
import { Activity, Database, Server, RefreshCw } from "lucide-react";

type DiagnosticsStep = {
  name?: string;
  ok?: boolean;
};

type DiagnosticsResult = {
  status?: string;
  steps?: DiagnosticsStep[];
};

export default function HealthPage() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [diagnosticsLoading, setDiagnosticsLoading] = useState(false);
  const [diagnostics, setDiagnostics] = useState<DiagnosticsResult | null>(null);
  const [diagnosticsError, setDiagnosticsError] = useState<string | null>(null);

  const checkHealth = () => {
    setLoading(true);
    fetch("/api/health")
      .then(res => res.json())
      .then(setHealth)
      .catch(e => setHealth({ status: "error", db: String(e) }))
      .finally(() => setLoading(false));
  };

  const runDiagnostics = async () => {
    setDiagnosticsLoading(true);
    setDiagnosticsError(null);
    setDiagnostics(null);

    console.info("admin.diagnostics", {
      stage: "request",
      surface: "admin_health",
      block: "DIAGNOSTICS_RUNNER",
      semantic_block: "DIAGNOSTICS_RUNNER",
      flow_id: "FLOW-ADMIN-OPS",
      evidence: "Task.md",
    });

    try {
      const response = await fetch("/api/diagnostics/run", { method: "POST" });
      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMessage = typeof payload?.detail === "string" ? payload.detail : "Diagnostics failed";
        throw new Error(errorMessage);
      }

      setDiagnostics(payload);
      console.info("admin.diagnostics", {
        stage: "success",
        status: typeof payload?.status === "string" ? payload.status : "unknown",
        steps_count: Array.isArray(payload?.steps) ? payload.steps.length : 0,
        telemetry_ready: true,
        evidence: "Task.md",
        surface: "admin_health",
        block: "DIAGNOSTICS_RUNNER",
        semantic_block: "DIAGNOSTICS_RUNNER",
        flow_id: "FLOW-ADMIN-OPS",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Diagnostics failed";
      setDiagnosticsError(message);
      console.info("admin.diagnostics", {
        stage: "error",
        error: message,
        evidence: "Task.md",
        surface: "admin_health",
        block: "DIAGNOSTICS_RUNNER",
        semantic_block: "DIAGNOSTICS_RUNNER",
        flow_id: "FLOW-ADMIN-OPS",
      });
    } finally {
      setDiagnosticsLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const isOk = health?.status === "ok" && health?.db === "connected";

  return (
    <div className="flex flex-col gap-6 py-6 pb-24 max-w-2xl mx-auto" data-testid="admin-health-page">
      <div className="flex justify-between items-center px-1">
        <h1 className="text-2xl font-black text-slate-900">Система</h1>
        <button onClick={checkHealth} className="p-2 bg-white border rounded-xl hover:bg-slate-50 transition-colors shadow-sm">
            <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      <div className={`p-6 rounded-3xl border shadow-sm flex items-center gap-4 ${isOk ? "bg-green-50 border-green-100" : "bg-rose-50 border-rose-100"}`}>
        <div className={`p-3 rounded-xl ${isOk ? "bg-green-100 text-green-600" : "bg-rose-100 text-rose-600"}`}>
            <Activity size={32} />
        </div>
        <div>
            <h2 className={`text-lg font-bold ${isOk ? "text-green-800" : "text-rose-800"}`}>
                {isOk ? "Все системы в норме" : "Обнаружены проблемы"}
            </h2>
            <p className={`text-sm ${isOk ? "text-green-600" : "text-rose-600"}`}>
                {health?.status === "error" ? "API недоступен." : "API доступен."} {health?.db === "connected" ? "База данных подключена." : "База данных: " + (health?.db || "ошибка")}
            </p>
        </div>
      </div>

      <div className="grid gap-3">
        <div className="bg-white p-4 rounded-2xl border border-slate-100 flex justify-between items-center">
            <div className="flex items-center gap-3">
                <Server size={20} className="text-slate-400" />
                <span className="font-bold text-slate-700">API Backend</span>
            </div>
            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded">ONLINE</span>
        </div>
        
        <div className="bg-white p-4 rounded-2xl border border-slate-100 flex justify-between items-center">
            <div className="flex items-center gap-3">
                <Database size={20} className="text-slate-400" />
                <span className="font-bold text-slate-700">Database</span>
            </div>
            <span className={`px-2 py-1 text-xs font-bold rounded ${health?.db === "connected" ? "bg-green-100 text-green-700" : "bg-rose-100 text-rose-700"}`}>
                {health?.db === "connected" ? "CONNECTED" : "ERROR"}
            </span>
        </div>
      </div>

      <section className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm" data-testid="admin-diagnostics-runner">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Diagnostics runner</h2>
            <p className="mt-1 text-sm text-slate-500">
              Запускает диагностический прогон и сохраняет evidence/telemetry для admin flow.
            </p>
          </div>
          <button
            type="button"
            onClick={runDiagnostics}
            disabled={diagnosticsLoading}
            data-testid="admin-diagnostics-run"
            className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
          >
            <RefreshCw size={16} className={diagnosticsLoading ? "animate-spin" : ""} />
            {diagnosticsLoading ? "Запуск…" : "Run diagnostics"}
          </button>
        </div>

        <div className="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-600" data-testid="admin-diagnostics-evidence">
          <div><span className="font-semibold text-slate-900">Evidence:</span> diagnostics runner response + Task.md summary</div>
          <div className="mt-1"><span className="font-semibold text-slate-900">Telemetry:</span> <code>admin.diagnostics</code> with request/success/error stages</div>
        </div>

        {diagnosticsError ? (
          <div className="mt-4 rounded-2xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-700" data-testid="admin-diagnostics-error">
            {diagnosticsError}
          </div>
        ) : null}

        {diagnostics ? (
          <div className="mt-4 space-y-3" data-testid="admin-diagnostics-result">
            <div className="flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-3">
              <span className="text-sm font-semibold text-slate-700">Runner status</span>
              <span data-testid="admin-diagnostics-status" className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold uppercase text-emerald-700">
                {diagnostics.status ?? "unknown"}
              </span>
            </div>

            <div className="grid gap-2" data-testid="admin-diagnostics-steps">
              {(diagnostics.steps ?? []).map((step) => (
                <div
                  key={step.name ?? "unknown"}
                  className="flex items-center justify-between rounded-2xl border border-slate-100 px-4 py-3 text-sm"
                  data-testid={`admin-diagnostics-step-${step.name ?? "unknown"}`}
                >
                  <span className="font-medium text-slate-700">{step.name ?? "unknown"}</span>
                  <span className={step.ok ? "text-emerald-600" : "text-rose-600"}>{step.ok ? "ok" : "failed"}</span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}
