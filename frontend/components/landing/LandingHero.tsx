import Link from "next/link";
import { ArrowRight, Star } from "lucide-react";

export function LandingHero() {
  return (
    <section className="relative pt-12 pb-20 px-6 overflow-hidden">
      {/* Background Decor */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-lg h-[500px] bg-gradient-to-b from-purple-200/40 to-transparent blur-3xl -z-10" />
      
      <div className="max-w-md mx-auto text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/60 border border-purple-100 shadow-sm animate-in fade-in zoom-in duration-500">
            <Star size={12} className="text-purple-600 fill-purple-600" />
            <span className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">14 дней бесплатно</span>
        </div>
        
        <h1 className="text-4xl font-black text-slate-900 leading-[1.1] tracking-tight">
          Твой личный астролог <br/>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-indigo-600">в кармане</span>
        </h1>
        
        <p className="text-lg text-slate-600 leading-relaxed">
          Персональные прогнозы, анализ личности и ответы на вопросы. Попробуй премиум-доступ бесплатно.
        </p>
        
        <div className="flex flex-col gap-3 pt-4">
            <Link 
                href="/start" 
                data-testid="start-cta"
                className="gradient-primary py-4 rounded-2xl font-bold text-lg shadow-xl shadow-purple-500/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2"
            >
                Попробовать 14 дней
                <ArrowRight size={20} />
            </Link>
            <p className="text-[10px] text-slate-400">
                Бесплатно. Отмена в любой момент.
            </p>
        </div>
      </div>
    </section>
  );
}
