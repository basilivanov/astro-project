"use client";

import { useEffect, useState } from "react";
import { Activity, Database, Server, RefreshCw } from "lucide-react";

export default function HealthPage() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const checkHealth = () => {
    setLoading(true);
    fetch("/api/health")
      .then(res => res.json())
      .then(setHealth)
      .catch(e => setHealth({ status: "error", db: String(e) }))
      .finally(() => setLoading(false));
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
    </div>
  );
}
