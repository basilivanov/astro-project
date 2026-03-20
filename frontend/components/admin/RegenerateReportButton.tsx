"use client";

import { RefreshCw, Check, X } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "../../hooks/useTelegram";

export function RegenerateReportButton({ reportId }: { reportId: string }) {
  const { initData } = useTelegram();
  const [loading, setLoading] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [reason, setReason] = useState("Улучшение качества / Исправление");
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const router = useRouter();

  const handleRegenerate = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (!reason.trim()) return;
    
    setLoading(true);
    setStatus("idle");
    try {
      const res = await fetch(`/api/admin/reports/${reportId}/regenerate_copy`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "X-Telegram-Auth": initData
        },
        body: JSON.stringify({ reason })
      });
      
      if (!res.ok) throw new Error("Failed");
      
      router.refresh();
      setStatus("success");
      setIsConfirming(false);
      
      // Clear success icon after delay, but don't refresh again
      setTimeout(() => {
          setStatus("idle");
      }, 3000);
      
    } catch (err) {
      console.error("Regeneration failed:", err);
      setStatus("error");
      setTimeout(() => setStatus("idle"), 3000);
    } finally {
      setLoading(false);
    }
  };

  if (isConfirming) {
      return (
          <div className="flex items-center gap-2 animate-in slide-in-from-right-2 duration-200">
              <input 
                type="text"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Причина..."
                className="text-[10px] px-2 py-1 border border-purple-200 rounded-lg outline-none focus:border-purple-500 w-32"
                autoFocus
              />
              <button 
                onClick={handleRegenerate}
                disabled={loading}
                className="p-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors shadow-sm"
                title="Подтвердить"
              >
                {loading ? <RefreshCw size={12} className="animate-spin" /> : <Check size={12} />}
              </button>
              <button 
                onClick={() => setIsConfirming(false)}
                disabled={loading}
                className="p-1.5 bg-slate-100 text-slate-500 rounded-lg hover:bg-slate-200 transition-colors"
                title="Отмена"
              >
                <X size={12} />
              </button>
          </div>
      )
  }

  return (
    <button 
      onClick={(e) => { e.preventDefault(); setIsConfirming(true); }}
      disabled={loading || status !== "idle"}
      className={`p-2 rounded-lg transition-all flex items-center gap-1 ${
          status === "success" ? "bg-green-50 text-green-600" :
          status === "error" ? "bg-rose-50 text-rose-600" :
          "text-slate-400 hover:text-purple-600 hover:bg-purple-50"
      }`}
      title="Перегенерировать копию"
    >
      {status === "success" ? <Check size={16} /> : 
       status === "error" ? <X size={16} /> :
       <RefreshCw size={16} className={loading ? "animate-spin" : ""} />}
    </button>
  );
}
