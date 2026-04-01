// ############################################################################
// AI_HEADER: MODULE_LAYOUT
// ROLE: Global layout for the admin UI.
// DEPENDENCIES: globals.css.
// GRACE_ANCHORS: [LAYOUT_ROOT]
// ############################################################################

import "./globals.css";

export const metadata = {
  title: "AstroGrace — Твой личный астролог",
  description: "Персональные прогнозы на каждый день. Узнай свою судьбу с AstroGrace.",
  icons: {
    icon: "/favicon.svg",
  },
  openGraph: {
    title: "AstroGrace — Твой личный астролог",
    description: "Персональные прогнозы на каждый день. Попробуй Premium бесплатно.",
    url: "https://app.astrograce.ru",
    siteName: "AstroGrace",
    images: [
      {
        url: "https://app.astrograce.ru/og-image.jpg", // Needs to be added to public/
        width: 1200,
        height: 630,
      },
    ],
    locale: "ru_RU",
    type: "website",
  },
};

// #START_BLOCK_LAYOUT_ROOT
import Script from 'next/script';
import BottomNav from '../components/BottomNav';
import { LegalFooterBlock } from '../components/legal-links';

const runtimeEnvironment =
  process.env.ENVIRONMENT ||
  process.env.NEXT_PUBLIC_ENVIRONMENT ||
  process.env.VERCEL_ENV ||
  process.env.NODE_ENV;

const environmentBadgeLabel =
  runtimeEnvironment && runtimeEnvironment.toLowerCase() === 'production' ? 'PROD' : 'DEV';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <head>
        <Script 
            src="https://telegram.org/js/telegram-web-app.js" 
            strategy="beforeInteractive" 
        />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
      </head>
      <body className="antialiased pb-24 min-h-screen selection:bg-purple-200 selection:text-purple-900" suppressHydrationWarning>
        <div className="fixed right-2 top-2 z-50 rounded bg-black/55 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-white/85 pointer-events-none select-none">
          {environmentBadgeLabel}
        </div>
        <main className="min-h-screen relative z-10">
            {children}
        </main>
        <footer className="border-t border-slate-200 bg-white/95 px-6 py-4 text-center text-xs text-slate-500">
          <LegalFooterBlock className="mx-auto max-w-4xl" compact />
        </footer>
        <BottomNav />
      </body>
    </html>
  );
}
// #END_BLOCK_LAYOUT_ROOT
