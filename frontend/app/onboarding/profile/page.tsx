"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTelegram } from "../../../hooks/useTelegram";
import GeoAutocomplete from "../../../components/GeoAutocomplete";
import { ArrowRight, Check, Calendar, User } from "lucide-react";
import { LEGAL_PUBLIC_DOMAIN, LegalIdentityBlock } from "../../../components/legal-links";
import {
    buildKnownTimeOnboardingContinuity,
    createInitialOnboardingProfileForm,
    isOnboardingProfileStepValid,
} from "./onboarding-profile-helpers";

export default function OnboardingPage() {
    const { user, initData } = useTelegram();
    const router = useRouter();
    const [step, setStep] = useState(0); // Start from Step 0 (Welcome)
    const [loading, setLoading] = useState(false);
    const [dataConsentAccepted, setDataConsentAccepted] = useState(true);
    
    const [form, setForm] = useState(createInitialOnboardingProfileForm);

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
                body: JSON.stringify({
                    full_name: form.full_name,
                    birth_date: form.birth_date,
                    birth_time: form.birth_time,
                    birth_time_known: form.birth_time_known,
                    birth_place: form.birth_place,
                    birth_lat: form.birth_lat,
                    birth_lon: form.birth_lon,
                    birth_timezone: form.birth_timezone,
                    current_timezone: currentTz
                })
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

    const knownTimeContinuity = buildKnownTimeOnboardingContinuity(form);
    const isStepValid = () => isOnboardingProfileStepValid(step, form) && (step !== 3 || dataConsentAccepted);

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col pb-32 pt-6 px-6 relative overflow-hidden">
            {/* Background Decor */}
            <div className="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-purple-100/50 to-transparent -z-10" />
            <div className="absolute -top-10 -right-10 w-40 h-40 bg-purple-200/30 rounded-full blur-3xl" />

            {/* Progress (Only for steps 1-3) */}
            {step > 0 && (
                <div className="flex gap-2 mb-8 mt-2 relative z-10">
                    {[1, 2, 3].map(i => (
                        <div key={i} className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${step >= i ? "bg-gradient-to-r from-purple-500 to-indigo-500 shadow-sm" : "bg-slate-200"}`}></div>
                    ))}
                </div>
            )}

            <div className="flex-1 flex flex-col justify-center relative z-10">
                {step === 0 && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom duration-700 text-center">
                        <div className="flex justify-center mb-6">
                            <div className="w-24 h-24 bg-gradient-to-br from-white to-purple-50 rounded-full flex items-center justify-center text-4xl shadow-xl shadow-purple-200 ring-4 ring-white">
                                ✨
                            </div>
                        </div>
                        <div className="space-y-3">
                            <h1 className="text-3xl font-black text-slate-900 tracking-tight">
                                Добро пожаловать <br/>
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-indigo-600">в AstroGrace</span>
                            </h1>
                            <p className="text-slate-500 text-lg leading-relaxed">
                                Мы создадим вашу натальную карту, чтобы давать точные прогнозы каждый день.
                            </p>
                        </div>

                        <div className="bg-white rounded-2xl p-5 border border-purple-100 shadow-sm text-left space-y-4">
                            <div className="flex items-start gap-3">
                                <div className="p-2.5 bg-purple-50 rounded-xl text-purple-600">📅</div>
                                <div>
                                    <h3 className="font-bold text-slate-800">Ежедневный навигатор</h3>
                                    <p className="text-sm text-slate-500 leading-snug">Узнайте, когда действовать, а когда отдохнуть.</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <div className="p-2.5 bg-indigo-50 rounded-xl text-indigo-600">🔮</div>
                                <div>
                                    <h3 className="font-bold text-slate-800">Личный астролог</h3>
                                    <p className="text-sm text-slate-500 leading-snug">Задавайте любые вопросы и получайте ответы.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {step === 1 && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-right duration-500">
                        <div className="space-y-2 text-center">
                            <h1 className="text-2xl font-black text-slate-900">Давайте знакомиться</h1>
                            <p className="text-slate-500">Как к вам обращаться?</p>
                        </div>
                        
                        <div className="space-y-5">
                            <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center gap-3 shadow-sm focus-within:ring-2 focus-within:ring-purple-100 transition-all">
                                <User className="text-purple-400" size={20} />
                                <input 
                                    type="text" 
                                    value={form.full_name}
                                    onChange={e => setForm({...form, full_name: e.target.value})}
                                    placeholder="Ваше имя"
                                    className="bg-transparent w-full outline-none placeholder-slate-400 text-slate-900 font-medium"
                                />
                            </div>
                            
                            <div className="space-y-2">
                                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider ml-1">Дата рождения</p>
                                <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center gap-3 shadow-sm focus-within:ring-2 focus-within:ring-purple-100 transition-all">
                                    <Calendar className="text-purple-400" size={20} />
                                    <input 
                                        type="date" 
                                        value={form.birth_date}
                                        onChange={e => setForm({...form, birth_date: e.target.value})}
                                        className="bg-transparent w-full outline-none text-slate-900 font-medium"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {step === 2 && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-right duration-500">
                        <div className="space-y-2 text-center">
                            <h1 className="text-2xl font-black text-slate-900">Время рождения</h1>
                            <p className="text-slate-500">Важно для расчета домов и Асцендента.</p>
                        </div>
                        
                        <div className="space-y-6">
                            <div className={`transition-all duration-300 ${!form.birth_time_known ? "opacity-40 grayscale blur-[1px]" : ""}`}>
                                <div className="bg-white border border-slate-200 rounded-3xl p-8 flex justify-center shadow-sm">
                                    <input 
                                        type="time" 
                                        value={form.birth_time}
                                        onChange={e => setForm({...form, birth_time: e.target.value})}
                                        className="bg-transparent text-6xl font-black outline-none text-center w-full text-slate-900"
                                    />
                                </div>
                            </div>
                            
                            <label className="flex items-center gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm cursor-pointer hover:bg-slate-50 transition-colors">
                                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${!form.birth_time_known ? "border-purple-500 bg-purple-500" : "border-slate-300"}`}>
                                    {!form.birth_time_known && <Check size={14} className="text-white" />}
                                </div>
                                <input 
                                    type="checkbox" 
                                    checked={!form.birth_time_known}
                                    onChange={e => setForm({...form, birth_time_known: !e.target.checked})}
                                    className="hidden"
                                />
                                <span className="text-sm font-medium text-slate-600">Я не знаю точное время</span>
                            </label>
                        </div>
                    </div>
                )}

                {step === 3 && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-right duration-500">
                        <div className="space-y-2 text-center">
                            <h1 className="text-2xl font-black text-slate-900">Место рождения</h1>
                            <p className="text-slate-500">Начните вводить город.</p>
                        </div>
                        
                        <GeoAutocomplete 
                            defaultValue={form.birth_place}
                            onSelect={(city, lat, lon, tz) => setForm({...form, birth_place: city, birth_lat: lat, birth_lon: lon, birth_timezone: tz})}
                        />

                        {knownTimeContinuity && (
                            <div
                                data-testid="onboarding-known-time-panel"
                                className="rounded-3xl border border-indigo-100 bg-indigo-50/80 p-5 shadow-sm"
                            >
                                <p className="text-xs font-bold uppercase tracking-[0.24em] text-indigo-500">Контур данных</p>
                                <p className="mt-2 text-base font-semibold text-slate-900">{knownTimeContinuity.label}</p>
                                <p data-testid="onboarding-known-time-summary" className="mt-1 text-sm text-slate-600">
                                    {knownTimeContinuity.value}
                                </p>
                                <div data-testid="onboarding-known-time-evidence" className="mt-3 space-y-1 text-sm font-medium text-indigo-900">
                                    {knownTimeContinuity.evidence.map((item) => (
                                        <p key={item}>{item}</p>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm leading-relaxed text-slate-600 shadow-sm">
                            <label className="flex items-start gap-3">
                                <input
                                    type="checkbox"
                                    checked={dataConsentAccepted}
                                    onChange={e => setDataConsentAccepted(e.target.checked)}
                                    className="mt-1 h-4 w-4 rounded border-slate-300 text-purple-600 focus:ring-purple-500"
                                />
                                <span>
                                    Продолжая, я принимаю условия сервиса и даю согласие на обработку данных для расчёта карты.
                                    {' '}<Link href="/legal/terms" className="font-semibold text-purple-700 hover:text-purple-800">Оферта</Link>,{' '}
                                    <Link href="/legal/privacy" className="font-semibold text-purple-700 hover:text-purple-800">Privacy / ПДн</Link>,{' '}
                                    <Link href="/legal/consent" className="font-semibold text-purple-700 hover:text-purple-800">Consent</Link>,{' '}
                                    <Link href="/legal/payments" className="font-semibold text-purple-700 hover:text-purple-800">Payments & refunds</Link>.
                                </span>
                            </label>
                            <div className="mt-3 rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-500">
                                <LegalIdentityBlock />
                                <p className="mt-1">Актуальный публичный домен: {LEGAL_PUBLIC_DOMAIN}</p>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Sticky Bottom Button */}
            <div className="fixed bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-white via-white/90 to-transparent z-50">
                <button 
                    onClick={handleNext}
                    disabled={!isStepValid() || loading}
                    className={`w-full py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-2 transition-all shadow-lg shadow-purple-200 ${isStepValid() ? "bg-gradient-to-r from-purple-600 to-indigo-600 text-white active:scale-[0.98]" : "bg-slate-100 text-slate-400 cursor-not-allowed"}`}
                >
                    {loading ? "Сохранение..." : step === 0 ? "Начать путешествие" : step === 3 ? "Рассчитать карту" : "Далее"}
                    {!loading && <ArrowRight size={20} />}
                </button>
            </div>
        </div>
    )
}
