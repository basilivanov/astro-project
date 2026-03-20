"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "../../../hooks/useTelegram";
import GeoAutocomplete from "../../../components/GeoAutocomplete";
import { ArrowLeft, Save, Loader2 } from "lucide-react";
import Link from "next/link";

const ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
];

export default function ProfileEditPage() {
    const { user, initData } = useTelegram();
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [profile, setProfile] = useState<any>(null);
    const [form, setForm] = useState({
        full_name: "",
        birth_date: "",
        birth_time: "12:00",
        birth_time_known: true,
        birth_place: "",
        birth_lat: 0,
        birth_lon: 0,
        birth_timezone: "",
        sun_sign: ""
    });

    useEffect(() => {
        if (user && initData) {
            fetch("/api/users/me", { headers: { "X-Telegram-Auth": initData } })
                .then(res => res.json())
                .then(data => {
                    setProfile(data);
                    setForm({
                        full_name: data.full_name || "",
                        birth_date: data.birth_date || "",
                        birth_time: data.birth_time || "12:00",
                        birth_time_known: data.birth_time_known ?? true,
                        birth_place: data.birth_place || "",
                        birth_lat: data.birth_lat || 0,
                        birth_lon: data.birth_lon || 0,
                        birth_timezone: data.birth_timezone || "",
                        sun_sign: data.sun_sign || ""
                    });
                })
                .catch(console.error);
        }
    }, [user, initData]);

    const handleSave = async () => {
        if (!user || !initData) return;
        setLoading(true);
        try {
            const currentTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
            const res = await fetch("/api/users/me", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "X-Telegram-Auth": initData
                },
                body: JSON.stringify({ ...form, current_timezone: currentTz })
            });
            if (res.ok) {
                router.push("/profile");
            } else {
                alert("Ошибка сохранения");
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (!profile) return <div className="p-10 text-center text-slate-400">Загрузка...</div>;

    return (
        <div className="p-6 space-y-6 pt-10 pb-32 bg-slate-50 min-h-screen">
            <div className="flex items-center gap-2 mb-4">
                <Link href="/profile" className="p-2 -ml-2 text-slate-400 hover:text-purple-600 transition-colors">
                    <ArrowLeft size={28} strokeWidth={1.5} />
                </Link>
                <h1 className="text-2xl font-bold text-slate-800">Настройки профиля</h1>
            </div>

            <div className="space-y-4">
                <section className="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm space-y-4">
                    <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-1">Имя</label>
                        <input 
                            type="text" 
                            value={form.full_name}
                            onChange={e => setForm({...form, full_name: e.target.value})}
                            className="w-full p-3 bg-slate-50 rounded-xl border-none focus:ring-2 focus:ring-purple-200 text-slate-800"
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-1">Дата рождения</label>
                        <input 
                            type="date" 
                            value={form.birth_date}
                            onChange={e => setForm({...form, birth_date: e.target.value})}
                            className="w-full p-3 bg-slate-50 rounded-xl border-none focus:ring-2 focus:ring-purple-200 text-slate-800"
                        />
                    </div>

                    <div className="space-y-3">
                        <div className="flex justify-between items-center ml-1">
                            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider">Время рождения</label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input 
                                    type="checkbox" 
                                    checked={!form.birth_time_known}
                                    onChange={e => setForm({...form, birth_time_known: !e.target.checked})}
                                    className="rounded border-slate-300 text-purple-600 focus:ring-purple-500"
                                />
                                <span className="text-[10px] font-bold text-slate-500 uppercase">Неизвестно</span>
                            </label>
                        </div>
                        {form.birth_time_known && (
                            <input 
                                type="time" 
                                value={form.birth_time}
                                onChange={e => setForm({...form, birth_time: e.target.value})}
                                className="w-full p-3 bg-slate-50 rounded-xl border-none focus:ring-2 focus:ring-purple-200 text-slate-800 animate-in fade-in duration-200"
                            />
                        )}
                    </div>

                    {!form.birth_date && (
                        <div>
                            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-1">Знак Зодиака (если нет даты)</label>
                            <select 
                                value={form.sun_sign}
                                onChange={e => setForm({...form, sun_sign: e.target.value})}
                                className="w-full p-3 bg-slate-50 rounded-xl border-none focus:ring-2 focus:ring-purple-200 text-slate-800 appearance-none"
                            >
                                <option value="">Выберите знак</option>
                                {ZODIAC_SIGNS.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>
                    )}

                    <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-1">Место рождения</label>
                        <GeoAutocomplete 
                            defaultValue={form.birth_place}
                            onSelect={(city, lat, lon, tz) => setForm({...form, birth_place: city, birth_lat: lat, birth_lon: lon, birth_timezone: tz})}
                        />
                    </div>
                </section>
            </div>

            <div className="fixed bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-slate-50 via-slate-50/90 to-transparent z-50">
                <button 
                    onClick={handleSave}
                    disabled={loading}
                    className="w-full bg-slate-900 text-white font-bold py-4 rounded-2xl hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-xl"
                >
                    {loading ? <Loader2 className="animate-spin" size={20} /> : <Save size={20} />}
                    Сохранить изменения
                </button>
            </div>
        </div>
    );
}
