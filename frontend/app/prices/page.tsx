"use client";

import { LandingProducts } from "../../components/landing/LandingProducts";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function PricesPage() {
  return (
    <div className="bg-white min-h-screen p-6 animate-in fade-in duration-500">
        <Link href="/" className="inline-flex items-center gap-2 text-slate-500 mb-6 hover:text-purple-600 transition-colors">
            <ArrowLeft size={20} />
            <span className="font-bold">Назад</span>
        </Link>
        <LandingProducts />
    </div>
  );
}
