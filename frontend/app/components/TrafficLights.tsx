import { Heart, Wallet, Activity } from "lucide-react";

export function TrafficLights({ lights }: any) {
    const colors: any = { green: "bg-emerald-500", yellow: "bg-amber-500", red: "bg-rose-500" };
    const bgColors: any = { 
        green: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400", 
        yellow: "bg-amber-500/10 border-amber-500/20 text-amber-400", 
        red: "bg-rose-500/10 border-rose-500/20 text-rose-400" 
    };

    const items = [
        { key: 'health', label: 'Тонус', icon: Activity },
        { key: 'money', label: 'Деньги', icon: Wallet },
        { key: 'love', label: 'Чувства', icon: Heart },
    ];

    return (
        <div className="grid grid-cols-3 gap-3">
            {items.map(item => {
                const status = lights?.[item.key] || 'gray';
                const colorClass = bgColors[status] || "bg-zinc-800 text-zinc-500 border-zinc-700";
                
                return (
                    <div key={item.key} className={`rounded-2xl p-3 py-4 flex flex-col items-center gap-2 border transition-all ${colorClass}`}>
                        <item.icon size={26} strokeWidth={2.5} />
                        <span className="text-[11px] font-bold uppercase tracking-wide opacity-90">{item.label}</span>
                        {/* <div className={`w-8 h-1 rounded-full mt-1 opacity-50 ${colors[status] || 'bg-zinc-700'}`}></div> */}
                    </div>
                )
            })}
        </div>
    )
}
