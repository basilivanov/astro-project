"use client";

import { useEffect, useState } from "react";
import { Users, Search, User, Calendar, Plus } from "lucide-react";
import Link from "next/link";
import { useDebounce } from "use-debounce";

import { useTelegram } from "../../../hooks/useTelegram";

export const dynamic = "force-dynamic";

export default function AdminUsersPage() {
  const { initData, isReady } = useTelegram();
  const [users, setUsers] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 500);
  const [loading, setLoading] = useState(true);

  const fetchUsers = async () => {
    if (!isReady) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/admin/users${debouncedSearch ? `?q=${debouncedSearch}` : ""}`, {
        headers: { "X-Telegram-Auth": initData }
      });
      const data = await res.json();
      setUsers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [debouncedSearch, isReady, initData]);

  const safeUsers = Array.isArray(users) ? users : [];

  const addDays = async (userId: string, days: number) => {
    const reason = prompt("Причина начисления?");
    if (!reason) return;
    await fetch(`/api/admin/users/${userId}/subscription/add-days`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "X-Telegram-Auth": initData
      },
      body: JSON.stringify({ days, reason })
    });
    fetchUsers();
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-black text-slate-900 flex items-center gap-3">
          <Users className="text-purple-600" size={32} />
          Пользователи
        </h1>
      </div>

      <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-50 bg-slate-50/30">
          <div className="relative max-w-md">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="text"
              placeholder="Поиск по имени, username или коду..."
              className="w-full pl-12 pr-4 py-3 bg-white border border-slate-200 rounded-2xl focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 outline-none transition-all shadow-sm"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-slate-50/50 text-slate-500 text-xs font-bold uppercase tracking-wider">
                <th className="px-6 py-4">Пользователь</th>
                <th className="px-6 py-4">Подписка до</th>
                <th className="px-6 py-4">Баланс</th>
                <th className="px-6 py-4">Хорары</th>
                <th className="px-6 py-4 text-right">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {safeUsers.length === 0 && !loading ? (
                <tr><td colSpan={5} className="text-center py-10 text-slate-400">Ничего не найдено</td></tr>
              ) : (
                safeUsers.map(u => (
                  <tr key={u.id} className="hover:bg-purple-50/30 transition-colors">
                    <td className="px-6 py-4">
                      <Link href={`/admin/users/${u.id}`} className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
                          <User size={20} />
                        </div>
                        <div>
                          <div className="font-bold text-slate-900">{u.full_name}</div>
                          <div className="text-xs text-slate-500">@{u.username}</div>
                        </div>
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-slate-600">
                        {u.subscription_active_until ? new Date(u.subscription_active_until).toLocaleDateString() : "Нет"}
                      </div>
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-slate-700">{u.balance} ₽</td>
                    <td className="px-6 py-4 font-mono font-bold text-purple-600">{u.horary_credits}</td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button onClick={() => addDays(u.id, 14)} className="px-3 py-1.5 bg-purple-50 text-purple-700 rounded-lg text-xs font-bold hover:bg-purple-100 transition-colors">+14д</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}