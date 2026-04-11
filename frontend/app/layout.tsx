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

const STALE_SERVER_ACTION_GUARD = `
(() => {
  if (typeof window === 'undefined') return;
  const shouldBlockStaleActionPost = (url, method) => {
    if (method !== 'POST') return false;
    if (!url) return false;
    try {
      const target = new URL(url, window.location.href);
      return target.origin === window.location.origin
        && (target.pathname === '/' || target.pathname === '/app' || target.pathname === '/_next' || target.pathname === '/_next/server');
    } catch {
      return false;
    }
  };

  const originalFetch = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const url = typeof input === 'string' ? input : input instanceof Request ? input.url : String(input);
    const method = (init?.method || (input instanceof Request ? input.method : 'GET') || 'GET').toUpperCase();
    if (shouldBlockStaleActionPost(url, method)) {
      console.warn('[server-action-guard] blocked stale POST', { url, method });
      return new Response(JSON.stringify({ blocked: true, reason: 'stale_server_action_guard' }), {
        status: 409,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    return originalFetch(input, init);
  };
})();
`;

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
        <Script id="stale-server-action-guard" strategy="beforeInteractive">
          {STALE_SERVER_ACTION_GUARD}
        </Script>
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
