"use client";
import { useState, useEffect } from "react";
import { Search, MapPin, Loader2 } from "lucide-react";

interface GeoSuggestion {
    id: string;
    name: string;
    admin1: string;
    country: string;
    lat: number;
    lon: number;
    label: string;
}

interface Props {
    onSelect: (city: string, lat: number, lon: number, tz: string) => void;
    defaultValue?: string;
}

export default function GeoAutocomplete({ onSelect, defaultValue }: Props) {
    const [query, setQuery] = useState(defaultValue || "");
    const [suggestions, setSuggestions] = useState<GeoSuggestion[]>([]);
    const [loading, setLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(false);

    const handleSelect = async (item: GeoSuggestion) => {
        setQuery(item.label);
        setIsOpen(false);
        setLoading(true);
        try {
            const res = await fetch(`/api/geo/timezone?lat=${item.lat}&lon=${item.lon}`);
            const data = await res.json();
            onSelect(item.label, item.lat, item.lon, data.timezone_id || "UTC");
        } catch (e) {
            console.error("TZ fetch fail", e);
            onSelect(item.label, item.lat, item.lon, "UTC");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const timer = setTimeout(() => {
            if (query.length > 2 && isOpen) {
                setLoading(true);
                fetch(`/api/geo/autocomplete?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        setSuggestions(Array.isArray(data) ? data : []);
                        setLoading(false);
                    })
                    .catch(() => setLoading(false));
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [query, isOpen]);

    return (
        <div className="relative">
            <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" size={20} />
                <input
                    type="text"
                    value={query}
                    onChange={(e) => {
                        setQuery(e.target.value);
                        setIsOpen(true);
                    }}
                    placeholder="Начните вводить город..."
                    className="w-full bg-zinc-900/50 backdrop-blur-xl border border-zinc-700/50 rounded-2xl py-4 pl-12 pr-4 text-white placeholder-zinc-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all shadow-inner shadow-black/20"
                />
                {loading && (
                    <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 text-purple-400 animate-spin" size={20} />
                )}
            </div>

            {isOpen && suggestions.length > 0 && (
                <div className="absolute z-50 w-full mt-2 bg-zinc-900/95 backdrop-blur-xl border border-zinc-700 rounded-2xl shadow-2xl max-h-60 overflow-y-auto overflow-x-hidden animate-in fade-in zoom-in-95 duration-200">
                    {suggestions.map((item) => (
                        <button
                            key={item.id}
                            className="w-full text-left px-4 py-3 hover:bg-white/10 flex items-center gap-3 border-b border-zinc-800/50 last:border-0 transition-colors"
                            onClick={() => handleSelect(item)}
                        >
                            <div className="bg-zinc-800 p-2 rounded-full text-zinc-400 shrink-0">
                                <MapPin size={16} />
                            </div>
                            <div className="truncate">
                                <p className="text-white font-medium text-sm truncate">{item.name}</p>
                                <p className="text-zinc-500 text-xs truncate">{item.admin1}, {item.country}</p>
                            </div>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
