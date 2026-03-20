"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Calendar, Coins, FileText, User as UserIcon, CreditCard, Share2, Gift, Sparkles, Loader2, Check, X, AlertCircle } from "lucide-react";
import { useTelegram } from "../../../../hooks/useTelegram";

type UserDetail = {
  id: string;
  telegram_id: number;
  full_name: string;
  username: string;
  balance: number;
  subscription_active_until: string | null;
  created_at: string;
  is_partner: boolean;
  referral_code: string;
  reports_count: number;
  referrals_count: number;
  recent_reports: { id: string; type: string; status: string; created_at: string }[];
  recent_transactions: { id: string; amount: number; type: string; status: string; created_at: string }[];
};

type ActiveAction = {
    type: 'addDays' | 'addBalance' | 'grant';
    days?: number;
    grantType?: "credits" | "report";
    itemType?: string;
    title: string;
    placeholder?: string;
    defaultValue?: string;
    inputType?: 'text' | 'number';
    needsAmount?: boolean;
} | null;

export default function AdminUserDetailPage({ params }: { params: { id: string } }) {
  const { initData, isReady } = useTelegram();
  const [user, setUser] = useState<UserDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [activeAction, setActiveAction] = useState<ActiveAction>(null);
  const [actionInput, setActionInput] = useState("");
  const [actionAmount, setActionAmount] = useState("");
  const [message, setMessage] = useState<{ text: string, type: 'success' | 'error' } | null>(null);

  const fetchUser = () => {
    if (!isReady) return;
    setLoading(true);
    fetch(`/api/admin/users/${params.id}`, {
        headers: { "X-Telegram-Auth": initData }
    })
      .then(res => {
          if (!res.ok) throw new Error("User not found");
          return res.json();
      })
      .then(setUser)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchUser();
  }, [params.id, isReady, initData]);

  const showMessage = (text: string, type: 'success' | 'error' = 'success') => {
      setMessage({ text, type });
      setTimeout(() => setMessage(null), 4000);
  }

  const handleActionSubmit = async () => {
    if (!activeAction) return;
    
    const reason = actionInput || activeAction.defaultValue || "Admin action";
    if (activeAction.type === 'addDays' && reason.length < 3) {
        showMessage("Причина слишком короткая", "error");
        return;
    }

    setActionLoading(true);
    try {
        let res;
        if (activeAction.type === 'addDays') {
            res = await fetch(`/api/admin/users/${params.id}/subscription/add-days`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-Telegram-Auth": initData },
                body: JSON.stringify({ days: activeAction.days, reason })
            });
        } else if (activeAction.type === 'addBalance') {
            res = await fetch(`/api/admin/users/${params.id}/balance/add`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-Telegram-Auth": initData },
                body: JSON.stringify({ amount: parseFloat(actionAmount || "0"), reason })
            });
        } else if (activeAction.type === 'grant') {
            let payload: any = { type: activeAction.grantType, reason };
            if (activeAction.grantType === 'credits') {
                payload.amount = parseInt(actionAmount || "3");
                payload.currency = "CRD";
            } else {
                payload.report_type = activeAction.itemType;
            }
            res = await fetch(`/api/admin/users/${params.id}/grant`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-Telegram-Auth": initData },
                body: JSON.stringify(payload)
            });
        }

        if (res && !res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Operation failed");
        }
        
        showMessage("Успешно выполнено!");
        setActiveAction(null);
        setActionInput("");
        setActionAmount("");
        fetchUser();
    } catch (e: any) {
        showMessage(e.message, "error");
    } finally {
        setActionLoading(false);
    }
  };

  const startAddDays = (days: number) => {
      setActiveAction({
          type: 'addDays',
          days,
          title: `Добавить ${days} дней подписки`,
          placeholder: "Причина...",
          defaultValue: days === 14 ? "Промо-триал" : "Бонус"
      });
      setActionInput(days === 14 ? "Промо-триал" : "Бонус");
  }

  const startAddBalance = () => {
      setActiveAction({
          type: 'addBalance',
          title: "Пополнить баланс (RUB)",
          placeholder: "Причина...",
          defaultValue: "Подарок от админа",
          needsAmount: true,
          inputType: 'number'
      });
      setActionAmount("100");
      setActionInput("Подарок от админа");
  }

  const startGrant = (grantType: "credits" | "report", itemType?: string) => {
      setActiveAction({
          type: 'grant',
          grantType,
          itemType,
          title: grantType === 'credits' ? "Выдать кредиты (Хорары)" : `Выдать отчет: ${itemType}`,
          placeholder: "Причина...",
          defaultValue: grantType === 'credits' ? "Бонусные вопросы" : "Бесплатный отчет",
          needsAmount: grantType === 'credits',
          inputType: grantType === 'credits' ? 'number' : 'text'
      });
      if (grantType === 'credits') setActionAmount("3");
      setActionInput(grantType === 'credits' ? "Бонусные вопросы" : "Бесплатный отчет");
  }

  if (loading && !user) return <div className="p-10 text-center text-slate-400">Загрузка...</div>;
  if (!user && !loading) return <div className="p-10 text-center text-slate-400">Пользователь не найден</div>;

  return (
    <div className="flex flex-col gap-6 py-6 pb-24">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/admin/users" className="p-2 -ml-2 text-slate-400 hover:text-slate-600">
            <ArrowLeft size={24} />
        </Link>
        <div>
            <h1 className="text-2xl font-black text-slate-900">{user?.full_name}</h1>
            <p className="text-slate-500 text-sm">@{user?.username} · ID {user?.telegram_id}</p>
        </div>
      </div>

      {/* Message Toast */}
      {message && (
          <div className={`fixed top-4 left-1/2 -translate-x-1/2 z-50 px-6 py-3 rounded-2xl shadow-xl flex items-center gap-3 animate-in fade-in slide-in-from-top-4 duration-300 ${
              message.type === 'success' ? 'bg-emerald-600 text-white' : 'bg-rose-600 text-white'
          }`}>
              {message.type === 'success' ? <Check size={20} /> : <AlertCircle size={20} />}
              <span className="text-sm font-bold">{message.text}</span>
          </div>
      )}

      {/* Action Dialog (Non-blocking replacement for prompt) */}
      {activeAction && (
          <div className="bg-white border-2 border-purple-100 rounded-3xl p-6 shadow-xl animate-in zoom-in-95 duration-200">
              <h3 className="font-bold text-slate-900 mb-4">{activeAction.title}</h3>
              <div className="flex flex-col gap-3">
                  {activeAction.needsAmount && (
                      <div className="flex flex-col gap-1">
                          <label className="text-[10px] font-bold text-slate-400 uppercase">Сумма/Количество</label>
                          <input 
                            type="number"
                            value={actionAmount}
                            onChange={(e) => setActionAmount(e.target.value)}
                            className="w-full px-4 py-2 bg-slate-50 border border-slate-100 rounded-xl outline-none focus:border-purple-500 font-mono font-bold"
                            autoFocus
                          />
                      </div>
                  )}
                  <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-slate-400 uppercase">Обоснование (Audit Reason)</label>
                      <input 
                        type="text"
                        value={actionInput}
                        onChange={(e) => setActionInput(e.target.value)}
                        placeholder={activeAction.placeholder}
                        className="w-full px-4 py-2 bg-slate-50 border border-slate-100 rounded-xl outline-none focus:border-purple-500"
                        autoFocus={!activeAction.needsAmount}
                      />
                  </div>
                  <div className="flex gap-2 mt-2">
                      <button 
                        onClick={handleActionSubmit}
                        disabled={actionLoading}
                        className="flex-1 bg-purple-600 text-white py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 hover:bg-purple-700 transition-colors"
                      >
                          {actionLoading ? <Loader2 size={18} className="animate-spin" /> : <Check size={18} />}
                          Подтвердить
                      </button>
                      <button 
                        onClick={() => { setActiveAction(null); setActionInput(""); setActionAmount(""); }}
                        className="px-4 py-3 bg-slate-100 text-slate-500 rounded-xl font-bold text-sm hover:bg-slate-200 transition-colors"
                      >
                          Отмена
                      </button>
                  </div>
              </div>
          </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm">
            <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-bold text-slate-400 uppercase">Подписка</span>
                <Calendar size={16} className="text-purple-400" />
            </div>
            <div className="font-bold text-slate-900 text-lg">
                {user?.subscription_active_until 
                    ? new Date(user.subscription_active_until).toLocaleDateString() 
                    : "Нет"}
            </div>
            <div className="flex gap-2 mt-1">
                <button onClick={() => startAddDays(14)} className="text-[10px] font-bold text-purple-600 hover:underline">
                    +14д
                </button>
                <button onClick={() => startAddDays(30)} className="text-[10px] font-bold text-purple-600 hover:underline">
                    +30д
                </button>
                <button onClick={() => startAddDays(3650)} className="text-[10px] font-bold text-indigo-600 hover:underline">
                    ∞ Безлимит
                </button>
            </div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm">
            <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-bold text-slate-400 uppercase">Баланс</span>
                <Coins size={16} className="text-amber-400" />
            </div>
            <div className="font-bold text-slate-900 text-lg">{user?.balance} ₽</div>
            <button onClick={startAddBalance} className="text-[10px] font-bold text-green-600 mt-1 hover:underline">
                +Пополнить
            </button>
        </div>
        
        <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm">
            <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-bold text-slate-400 uppercase">Отчеты</span>
                <FileText size={16} className="text-blue-400" />
            </div>
            <div className="font-bold text-slate-900 text-lg">{user?.reports_count}</div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm">
            <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-bold text-slate-400 uppercase">Рефералы</span>
                <Share2 size={16} className="text-pink-400" />
            </div>
            <div className="font-bold text-slate-900 text-lg">{user?.referrals_count}</div>
            <div className="text-[10px] text-slate-400 font-mono mt-1">{user?.referral_code}</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-slate-900 rounded-3xl p-6 text-white shadow-xl shadow-slate-200">
          <h3 className="font-bold text-sm uppercase tracking-widest text-slate-400 mb-4 flex items-center gap-2">
              <Gift size={16} />
              Быстрые подарки
          </h3>
          <div className="grid grid-cols-2 gap-3">
              <button 
                onClick={() => startGrant("credits")} 
                disabled={actionLoading}
                className="flex flex-col items-center gap-2 bg-white/10 hover:bg-white/20 p-4 rounded-2xl transition-all"
              >
                  <Sparkles className="text-amber-400" size={24} />
                  <span className="text-xs font-bold text-center">3 Хорара</span>
              </button>
              <button 
                onClick={() => startGrant("report", "natal_master")} 
                disabled={actionLoading}
                className="flex flex-col items-center gap-2 bg-white/10 hover:bg-white/20 p-4 rounded-2xl transition-all"
              >
                  <FileText className="text-blue-400" size={24} />
                  <span className="text-xs font-bold text-center">Натальная</span>
              </button>
              <button 
                onClick={() => startGrant("report", "synastry")} 
                disabled={actionLoading}
                className="flex flex-col items-center gap-2 bg-white/10 hover:bg-white/20 p-4 rounded-2xl transition-all"
              >
                  <Share2 className="text-pink-400" size={24} />
                  <span className="text-xs font-bold text-center">Синастрия</span>
              </button>
              <button 
                onClick={() => startGrant("report", "solar_return")} 
                disabled={actionLoading}
                className="flex flex-col items-center gap-2 bg-white/10 hover:bg-white/20 p-4 rounded-2xl transition-all"
              >
                  <Sparkles className="text-orange-400" size={24} />
                  <span className="text-xs font-bold text-center">Соляр</span>
              </button>
              <button 
                onClick={() => startGrant("report", "year_forecast")} 
                disabled={actionLoading}
                className="flex flex-col items-center gap-2 bg-white/10 hover:bg-white/20 p-4 rounded-2xl transition-all"
              >
                  <Calendar className="text-emerald-400" size={24} />
                  <span className="text-xs font-bold text-center">Прогноз Год</span>
              </button>
          </div>
          {actionLoading && !activeAction && (
              <div className="mt-4 flex justify-center">
                  <Loader2 className="animate-spin text-purple-400" />
              </div>
          )}
      </div>

      {/* Reports List */}
      <div className="flex flex-col gap-3">
        <h3 className="font-bold text-slate-800 text-lg px-1">Последние отчеты</h3>
        {!user?.recent_reports || user.recent_reports.length === 0 ? (
            <div className="p-6 bg-slate-50 rounded-2xl text-center text-sm text-slate-400">Нет отчетов</div>
        ) : (
            user.recent_reports.map(r => (
                <Link key={r.id} href={`/reports/${r.id}`} className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm flex justify-between items-center">
                    <div>
                        <div className="font-bold text-sm text-slate-800">{r.type}</div>
                        <div className="text-[10px] text-slate-400">{new Date(r.created_at).toLocaleDateString()}</div>
                    </div>
                    <span className={`text-[10px] font-bold uppercase px-2 py-1 rounded ${
                        r.status === 'completed' ? 'bg-green-50 text-green-600' : 'bg-amber-50 text-amber-600'
                    }`}>
                        {r.status}
                    </span>
                </Link>
            ))
        )}
      </div>

      {/* Transactions List */}
      <div className="flex flex-col gap-3">
        <h3 className="font-bold text-slate-800 text-lg px-1">Транзакции</h3>
        {!user?.recent_transactions || user.recent_transactions.length === 0 ? (
            <div className="p-6 bg-slate-50 rounded-2xl text-center text-sm text-slate-400">Нет транзакций</div>
        ) : (
            user.recent_transactions.map(t => (
                <div key={t.id} className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm flex justify-between items-center">
                    <div>
                        <div className="font-bold text-sm text-slate-800">{t.type}</div>
                        <div className="text-[10px] text-slate-400">{new Date(t.created_at).toLocaleDateString()}</div>
                    </div>
                    <span className="font-mono font-bold text-slate-900">
                        {t.amount} ₽
                    </span>
                </div>
            ))
        )}
      </div>
    </div>
  );
}
