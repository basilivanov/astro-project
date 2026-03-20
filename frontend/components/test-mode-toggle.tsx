"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { FlaskConical } from "lucide-react";
import { useState, useEffect } from "react";

export function TestModeToggle() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  
  const [isEnabled, setIsEnabled] = useState(false);

  useEffect(() => {
    setIsEnabled(searchParams.get("show_test") === "true");
  }, [searchParams]);

  const toggle = () => {
    const params = new URLSearchParams(searchParams.toString());
    if (!isEnabled) {
      params.set("show_test", "true");
    } else {
      params.delete("show_test");
    }
    router.push(`${pathname}?${params.toString()}`);
  };

  return (
    <button
      onClick={toggle}
      className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-lg transition-all ${
        isEnabled 
          ? "bg-amber-100 text-amber-700 shadow-sm" 
          : "text-slate-500 hover:bg-slate-50 hover:text-slate-700"
      }`}
    >
      <FlaskConical size={20} className={isEnabled ? "animate-pulse" : ""} />
      <span className="font-medium text-sm">Тестовые данные</span>
      <div className={`ml-auto w-8 h-4 rounded-full relative transition-colors ${isEnabled ? "bg-amber-400" : "bg-slate-300"}`}>
        <div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full transition-all ${isEnabled ? "left-4.5" : "left-0.5"}`} />
      </div>
    </button>
  );
}
