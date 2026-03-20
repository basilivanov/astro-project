"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { 
  LayoutDashboard, 
  Users, 
  FileText, 
  Send, 
  ListTodo, 
  MessageSquare, 
  Settings,
  Menu,
  X,
  Contact,
  CreditCard,
  Activity,
  Shield
} from "lucide-react";
import { TestModeToggle } from "./test-mode-toggle";
import { AdminReferralWidget } from "./AdminReferralWidget";
import { cn } from "../lib/utils";

const NAV_ITEMS = [
  { href: "/admin/dashboard", icon: LayoutDashboard, label: "Дашборд" },
  { href: "/admin/reports", icon: FileText, label: "Отчеты" },
  { href: "/admin/users", icon: Users, label: "Пользователи" },
  { href: "/admin/tickets", icon: MessageSquare, label: "Тикеты" },
  { href: "/admin/broadcast", icon: Send, label: "Рассылка" },
  { href: "/admin/audit", icon: Shield, label: "Аудит" },
];

const TOOLS_ITEMS = [
    { href: "/admin/health", icon: Activity, label: "Здоровье" },
];

const MOBILE_MAIN = [
  "/admin/dashboard", 
  "/admin/reports", 
  "/admin/users", 
];

export function AdminNav() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);

  return (
    <>
      {/* --- Desktop Sidebar --- */}
      <aside className="hidden md:flex w-64 bg-white border-r border-slate-200 flex-col fixed inset-y-0 z-30">
        <div className="h-16 flex items-center px-6 border-b border-slate-100">
          <span className="text-xl font-black tracking-tight bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
            AstroAdmin
          </span>
        </div>
        
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group",
                isActive(item.href) 
                  ? "bg-purple-50 text-purple-700 font-medium" 
                  : "text-slate-600 hover:bg-slate-50 hover:text-purple-600"
              )}
            >
              <item.icon size={20} className={cn("transition-transform", !isActive(item.href) && "group-hover:scale-110")} />
              <span className="text-sm">{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-100 space-y-3 bg-slate-50/50">
          {TOOLS_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 text-slate-500 hover:text-purple-600 transition-colors rounded-lg hover:bg-white",
                isActive(item.href) && "bg-white text-purple-600 shadow-sm"
              )}
            >
              <item.icon size={20} />
              <span className="text-sm font-medium">{item.label}</span>
            </Link>
          ))}
          <AdminReferralWidget />
          <TestModeToggle />
          <Link href="/profile" className="flex items-center gap-3 px-3 py-2 text-slate-400 hover:text-slate-600 transition-colors">
            <Settings size={20} />
            <span className="text-sm font-medium">Настройки</span>
          </Link>
        </div>
      </aside>

      {/* --- Mobile Bottom Nav --- */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 pb-safe z-40 flex justify-around items-center h-16 px-2 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.02)]">
        {NAV_ITEMS.filter(i => MOBILE_MAIN.includes(i.href)).map(item => (
           <Link 
             key={item.href} 
             href={item.href}
             className={cn(
               "flex flex-col items-center gap-1 p-2 rounded-xl transition-all",
               isActive(item.href) ? "text-purple-600" : "text-slate-400 active:scale-95"
             )}
           >
             <item.icon size={24} strokeWidth={isActive(item.href) ? 2.5 : 2} />
             <span className="text-[10px] font-medium">{item.label}</span>
           </Link>
        ))}
        
        {/* Menu Button */}
        <button 
          onClick={() => setMobileMenuOpen(true)}
          className="flex flex-col items-center gap-1 p-2 text-slate-400 active:scale-95"
        >
          <Menu size={24} />
          <span className="text-[10px] font-medium">Меню</span>
        </button>
      </nav>

      {/* --- Mobile Menu Overlay --- */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-50 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="absolute right-0 top-0 bottom-0 w-[80%] max-w-[300px] bg-white shadow-2xl p-5 flex flex-col animate-in slide-in-from-right duration-300">
            <div className="flex justify-between items-center mb-6">
              <span className="text-lg font-black text-slate-900">Меню</span>
              <button onClick={() => setMobileMenuOpen(false)} className="p-2 bg-slate-100 rounded-full text-slate-500">
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-6">
               {/* Sections */}
               <div className="space-y-1">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Разделы</p>
                  {NAV_ITEMS.map(item => (
                    <Link 
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={cn(
                        "flex items-center gap-3 px-3 py-3 rounded-xl transition-colors",
                        isActive(item.href) ? "bg-purple-50 text-purple-700" : "text-slate-600 hover:bg-slate-50"
                      )}
                    >
                      <item.icon size={20} />
                      <span className="font-medium">{item.label}</span>
                    </Link>
                  ))}
               </div>

               {/* Utils */}
               <div className="space-y-3 pt-4 border-t border-slate-100">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Инструменты</p>
                  
                  {TOOLS_ITEMS.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className="flex items-center gap-3 px-3 py-2 text-slate-600 hover:bg-slate-50 rounded-xl transition-colors"
                    >
                      <item.icon size={20} />
                      <span className="font-medium">{item.label}</span>
                    </Link>
                  ))}

                  <AdminReferralWidget />
                  <TestModeToggle />
               </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
