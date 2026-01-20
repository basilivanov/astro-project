"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Sparkles, User, PlusCircle } from 'lucide-react';
import clsx from 'clsx';

export default function BottomNav() {
  const pathname = usePathname();
  if (
    pathname === "/admin" ||
    pathname.startsWith("/clients") ||
    pathname.startsWith("/reports/")
  ) {
    return null;
  }
  
  const navItems = [
    { href: '/', icon: Home, label: 'Сегодня' },
    { href: '/reports', icon: Sparkles, label: 'Прогнозы' },
    { href: '/create', icon: PlusCircle, label: 'Создать' },
    { href: '/profile', icon: User, label: 'Профиль' },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-[#1c1c1e] border-t border-zinc-800 pb-safe pt-3 px-6 flex justify-between items-center z-50 h-20">
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        return (
            <Link key={item.href} href={item.href} className={clsx("flex flex-col items-center gap-1 transition-colors", isActive ? 'text-purple-400' : 'text-zinc-500')}>
                <item.icon size={24} strokeWidth={isActive ? 2.5 : 2} />
                <span className="text-[10px] font-medium">{item.label}</span>
            </Link>
        )
      })}
    </nav>
  );
}
