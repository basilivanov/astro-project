"use client";

import { useEffect, useState } from "react";
import { Search, User } from "lucide-react";
import { useTelegram } from "../../../hooks/useTelegram";

type AuditLog = {
  id: string;
  action: string;
  reason: string;
  details: string;
  created_at: string;
  admin_name: string;
  target_user_name: string;
};

export default function AuditPage() {
  const { initData, isReady } = useTelegram();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchLogs = () => {
    if (!isReady) return;
    setLoading(true);
    fetch("/api/admin/audit", {
        headers: { "X-Telegram-Auth": initData }
    })
      .then(res => res.json())
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLogs();
  }, [isReady, initData]);

  return (
    <div className="flex flex-col gap-6 py-6 pb-24">
      <div className="flex flex-col gap-4 sticky top-0 bg-slate-50 z-10 pb-2 px-1">
        <h1 className="text-2xl font-black text-slate-900">Аудит действий</h1>
      </div>

      <div className="space-y-3">
        {logs.map(log => (
            <div key={log.id} className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm text-sm">
                <div className="flex justify-between items-start mb-2">
                    <div className="font-mono text-xs text-slate-400 bg-slate-50 px-2 py-1 rounded">
                        {log.action}
                    </div>
                    <div className="text-xs text-slate-400">
                        {new Date(log.created_at).toLocaleString()}
                    </div>
                </div>
                
                <div className="flex items-center gap-2 mb-2">
                    <span className="font-bold text-purple-700">{log.admin_name}</span>
                    <span className="text-slate-300">→</span>
                    <span className="font-bold text-slate-700">{log.target_user_name}</span>
                </div>
                
                {log.reason && (
                    <div className="mb-2 text-slate-600 italic">
                        "{log.reason}"
                    </div>
                )}
                
                {log.details && (
                    <pre className="text-[10px] text-slate-500 bg-slate-50 p-2 rounded overflow-x-auto">
                        {log.details}
                    </pre>
                )}
            </div>
        ))}
        {logs.length === 0 && !loading && (
            <div className="text-center py-10 text-slate-400">Пусто</div>
        )}
      </div>
    </div>
  );
}