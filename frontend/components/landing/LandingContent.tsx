"use client";

import { useEffect } from "react";
import { LandingHero } from "./LandingHero";
import { LandingFeatures } from "./LandingFeatures";
import { LandingProducts } from "./LandingProducts";
import { LandingFAQ } from "./LandingFAQ";
import Link from "next/link";
import { trackEvent } from "../../lib/analytics";

export function LandingContent() {
  useEffect(() => {
    trackEvent("landing_view");
  }, []);

  return (
    <div className="bg-white min-h-screen pb-24 animate-in fade-in duration-500">
      <LandingHero />
      <LandingFeatures />
      <LandingProducts />
      <LandingFAQ />
      
      <footer className="p-6 text-center text-[10px] text-slate-400 border-t border-slate-100">
        <div className="flex justify-center gap-4 mb-2">
            <Link href="/legal/terms" className="hover:text-purple-600 transition-colors">Оферта</Link>
            <Link href="/legal/privacy" className="hover:text-purple-600 transition-colors">Конфиденциальность</Link>
        </div>
        <p>AstroGrace AI © 2026</p>
      </footer>
    </div>
  );
}
