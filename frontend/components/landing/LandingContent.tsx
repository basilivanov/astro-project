"use client";

import { useEffect } from "react";
import { LandingHero } from "./LandingHero";
import { LandingFeatures } from "./LandingFeatures";
import { LandingProducts } from "./LandingProducts";
import { LandingFAQ } from "./LandingFAQ";
import LegalLinks from "../legal-links";
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
        <LegalLinks className="mb-2 flex flex-wrap justify-center gap-4" linkClassName="transition-colors hover:text-purple-600" />
        <p>AstroGrace AI © 2026</p>
      </footer>
    </div>
  );
}
