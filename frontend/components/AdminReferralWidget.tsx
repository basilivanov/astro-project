"use client";

import { useEffect, useState } from "react";
import { useTelegram } from "../hooks/useTelegram";
import { Copy, Check, Gift } from "lucide-react";

export function AdminReferralWidget() {
    const { user, initData } = useTelegram();
    const [referralCode, setReferralCode] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        if (user && initData) {
            fetch("/api/users/me", { headers: { "X-Telegram-Auth": initData } })
                .then(res => res.json())
                .then(data => {
                    if (data?.referral_code) {
                        setReferralCode(data.referral_code);
                    }
                })
                .catch(console.error);
        }
    }, [user, initData]);

    if (!referralCode) return null;

    const link = `https://t.me/AstroGraceBot?start=ref_${referralCode}`;

    const copyToClipboard = () => {
        navigator.clipboard.writeText(link);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="mx-3 mb-2 p-3 bg-gradient-to-br from-purple-50 to-white border border-purple-100 rounded-xl shadow-sm">
            <div className="flex items-center gap-2 mb-2 text-purple-700">
                <Gift size={14} />
                <span className="text-xs font-bold uppercase tracking-wider">Моя ссылка</span>
            </div>
            <button 
                onClick={copyToClipboard}
                className="w-full flex items-center justify-between gap-2 px-2 py-1.5 bg-white border border-purple-100 rounded-lg text-xs text-slate-600 hover:border-purple-300 transition-colors group"
            >
                <span className="truncate max-w-[120px] font-mono opacity-80">ref_{referralCode}</span>
                {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} className="text-slate-400 group-hover:text-purple-500" />}
            </button>
        </div>
    );
}
