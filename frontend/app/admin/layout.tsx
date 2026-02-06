import Link from "next/link";
import { Suspense } from "react";
import { 
  LayoutDashboard, 
  Users, 
  FileText, 
  Send, 
  ListTodo, 
  MessageSquare, 
  Settings 
} from "lucide-react";
import { TestModeToggle } from "../../components/test-mode-toggle";
import { AdminReferralWidget } from "../../components/AdminReferralWidget";

const NAV_ITEMS = [
  { href: "/admin/dashboard", icon: LayoutDashboard, label: "Дашборд" },
  { href: "/admin/users", icon: Users, label: "Пользователи" },
  { href: "/admin/clients", icon: Users, label: "Клиенты (CRM)" },
  { href: "/admin/reports", icon: FileText, label: "Отчеты" },
  { href: "/admin/broadcast", icon: Send, label: "Рассылка" },
  { href: "/admin/tasks", icon: ListTodo, label: "Задачи" },
  { href: "/admin/tickets", icon: MessageSquare, label: "Тикеты" },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-50 flex font-sans">
      {/* Sidebar Desktop */}
      <aside className="w-64 bg-white border-r border-slate-200 hidden md:flex flex-col fixed inset-y-0 z-20">
        <div className="h-16 flex items-center px-6 border-b border-slate-100">
          <span className="text-xl font-black tracking-tight bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
            AstroAdmin
          </span>
        </div>
        
        <nav className="flex-1 p-4 space-y-1">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 hover:text-purple-600 transition-colors group"
            >
              <item.icon size={20} className="group-hover:scale-110 transition-transform" />
              <span className="font-medium text-sm">{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-100 space-y-2">
          <AdminReferralWidget />
          <Suspense fallback={<div className="h-10 w-full animate-pulse bg-slate-50 rounded-lg" />}>
            <TestModeToggle />
          </Suspense>
          <Link href="/profile" className="flex items-center gap-3 px-3 py-2 text-slate-400 hover:text-slate-600 transition-colors">
            <Settings size={20} />
            <span className="text-sm font-medium">Настройки</span>
          </Link>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 md:pl-64 min-h-screen">
        <div className="max-w-7xl mx-auto">
            {children}
        </div>
      </main>
    </div>
  );
}
