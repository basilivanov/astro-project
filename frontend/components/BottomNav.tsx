"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Calendar, ShoppingBag, User } from 'lucide-react';
import clsx from 'clsx';

export default function BottomNav() {
  const pathname = usePathname();
  if (
    pathname === "/admin" ||
    pathname.startsWith("/admin/") ||
    pathname.startsWith("/create") ||
    pathname.startsWith("/start") ||
    pathname.startsWith("/onboarding") ||
    pathname.startsWith("/profile/edit") ||
    pathname.startsWith("/read/")
  ) {
    return null;
  }
  
  const navItems = [
    { href: '/', icon: Home, label: 'Сегодня' },
    { href: '/week', icon: Calendar, label: 'Неделя' },
    { href: '/reports', icon: ShoppingBag, label: 'Магазин' },
    { href: '/profile', icon: User, label: 'Профиль' },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-lg border-t border-purple-100 pb-safe pt-3 px-6 flex justify-between items-center z-50 h-20 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.02)]">
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        return (
            <Link key={item.href} href={item.href} className={clsx("flex flex-col items-center gap-1 transition-colors", isActive ? 'text-purple-600' : 'text-slate-400 hover:text-purple-400')}>
                <item.icon size={24} strokeWidth={isActive ? 2.5 : 2} />
                <span className="text-[10px] font-medium">{item.label}</span>
            </Link>
        )
      })}
    </nav>
  );
}
