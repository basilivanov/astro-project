"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "../hooks/useTelegram";
import GeoAutocomplete from "../components/GeoAutocomplete";
import { ArrowRight, Check, Clock, Calendar, User, MapPin } from "lucide-react";

export default function OnboardingPage() {
    const { user } = useTelegram();
    const router = useRouter();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    
    const [form, setForm] = useState({
        full_name: "",
        birth_date: "",
        birth_time: "12:00",
        birth_time_known: true,
        birth_place: "",
        birth_lat: 0,
        birth_lon: 0
    });

    useEffect(() => {
        if (user && !form.full_name) {
            setForm(prev => ({ ...prev, full_name: user.first_name || "" }));
        }
    }, [user]);

    const handleNext = () => {
        if (step < 3) {
            setStep(step + 1);
        } else {
            submitForm();
        }
    };

    const submitForm = async () => {
        if (!user) return;
        setLoading(true);
        try {
            const res = await fetch("/api/users/me", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "X-Telegram-ID": user.id.toString()
                },
                body: JSON.stringify(form)
            });
            if (res.ok) {
                router.push("/");
            } else {
                alert("Ошибка сохранения");
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const isStepValid = () => {
        if (step === 1) return form.full_name.length > 1 && form.birth_date.length > 0;
        if (step === 2) return !form.birth_time_known || form.birth_time.length > 0;
        if (step === 3) return form.birth_place.length > 0;
        return false;
    };

    return (
        <div className="min-h-screen bg-black text-white p-6 flex flex-col justify-between pb-safe pt-safe">
            {/* Progress */}
            <div className="flex gap-2 mb-8 mt-4">
                {[1, 2, 3].map(i => (
                    <div key={i} className={`h-1 flex-1 rounded-full transition-all duration-500 ${step >= i ? "bg-purple-500" : "bg-zinc-800"}`}></div>
                ))}
            </div>

            <div className="flex-1 flex flex-col justify-center">
                {step === 1 && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-right duration-500">
                        <div className="space-y-2">
                            <h1 className="text-3xl font-bold">Давайте знакомиться</h1>
                            <p className="text-zinc-500">Чтобы звезды говорили именно про вас.</p>
                        </div>
                        
                        <div className="space-y-4">
                            <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-4 flex items-center gap-3">
                                <User className="text-zinc-500" size={20} />
                                <input 
                                    type="text" 
                                    value={form.full_name}
                                    onChange={e => setForm({...form, full_name: e.target.value})}
                                    placeholder="Ваше имя"
                                    className="bg-transparent w-full outline-none placeholder-zinc-600"
                                />
                            </div>
                            
                            <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-4 flex items-center gap-3">
                                <Calendar className="text-zinc-500" size={20} />
                                <input 
                                    type="date" 
                                    value={form.birth_date}
                                    onChange={e => setForm({...form, birth_date: e.target.value})}
                                    className="bg-transparent w-full outline-none placeholder-zinc-600 text-white scheme-dark"
                                />
                            </div>
                        </div>
                    </div>
                )}

                {step === 2 && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-right duration-500">
                        <div className="space-y-2">
                            <h1 className="text-3xl font-bold">Во сколько вы родились?</h1>
                            <p className="text-zinc-500">Это нужно для расчета домов и Асцендента.</p>
                        </div>
                        
                        <div className="space-y-6">
                            <div className={`transition-all ${!form.birth_time_known ? "opacity-30 pointer-events-none grayscale" : ""}`}>
                                <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6 flex justify-center">
                                    <input 
                                        type="time" 
                                        value={form.birth_time}
                                        onChange={e => setForm({...form, birth_time: e.target.value})}
                                        className="bg-transparent text-5xl font-bold outline-none text-center w-full scheme-dark"
                                    />
                                </div>
                            </div>
                            
                            <label className="flex items-center gap-3 bg-zinc-900/30 p-4 rounded-xl border border-zinc-800/50 cursor-pointer">
                                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${!form.birth_time_known ? "border-purple-500 bg-purple-500" : "border-zinc-600"}`}>
                                    {!form.birth_time_known && <Check size={14} className="text-white" />}
                                </div>
                                <input 
                                    type="checkbox" 
                                    checked={!form.birth_time_known}
                                    onChange={e => setForm({...form, birth_time_known: !e.target.checked})}
                                    className="hidden"
                                />
                                <span className="text-sm font-medium">Я не знаю точное время</span>
                            </label>
                        </div>
                    </div>
                )}

                {step === 3 && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-right duration-500">
                        <div className="space-y-2">
                            <h1 className="text-3xl font-bold">Где это было?</h1>
                            <p className="text-zinc-500">Место рождения определяет вашу судьбу.</p>
                        </div>
                        
                        <GeoAutocomplete 
                            defaultValue={form.birth_place}
                            onSelect={(city, lat, lon) => setForm({...form, birth_place: city, birth_lat: lat, birth_lon: lon})}
                        />
                    </div>
                )}
            </div>

            <button 
                onClick={handleNext}
                disabled={!isStepValid() || loading}
                className={`w-full py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-2 transition-all ${isStepValid() ? "bg-white text-black active:scale-95" : "bg-zinc-800 text-zinc-500"}`}
            >
                {loading ? "Сохранение..." : step === 3 ? "Запустить Космос" : "Далее"}
                {!loading && <ArrowRight size={20} />}
            </button>
        </div>
    )
}
