import { Moon } from "lucide-react";

export function MoonCard({ sign, phase, emoji, vibe }: any) {
  const signs: any = { 
    Aries: "Овен ♈", Taurus: "Телец ♉", Gemini: "Близнецы ♊", Cancer: "Рак ♋", 
    Leo: "Лев ♌", Virgo: "Дева ♍", Libra: "Весы ♎", Scorpio: "Скорпион ♏", 
    Sagittarius: "Стрелец ♐", Capricorn: "Козерог ♑", Aquarius: "Водолей ♒", Pisces: "Рыбы ♓" 
  };

  return (
    <div className="bg-gradient-to-br from-indigo-900 to-purple-900 rounded-3xl p-6 text-white shadow-xl shadow-purple-900/20 border border-white/10 relative overflow-hidden">
        <div className="absolute -top-10 -right-10 w-32 h-32 bg-purple-500/30 blur-3xl rounded-full"></div>
        
        <div className="relative z-10">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <p className="text-purple-200 text-sm font-medium mb-1 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                        {phase}
                    </p>
                    <h2 className="text-3xl font-bold tracking-tight">{signs[sign] || sign}</h2>
                </div>
                <div className="text-5xl filter drop-shadow-2xl grayscale-0">{emoji}</div>
            </div>
            
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/5 mt-2">
                <p className="text-sm leading-relaxed text-purple-50 font-medium">
                    {vibe}
                </p>
            </div>
        </div>
    </div>
  );
}
