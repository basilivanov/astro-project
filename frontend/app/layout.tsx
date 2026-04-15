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

const DEV_RUNTIME_BADGE_ROUTE_GATE = `
(() => {
  if (typeof window === 'undefined' || typeof document === 'undefined') return;
  const win = window;
  const existing = win.__ASTRO_RUNTIME_BADGE_ROUTE_GATE__;
  if (existing && typeof existing.dispose === 'function') {
    existing.dispose();
  }

  const badgeSelector = '[data-runtime-badge-route-gate="day-home-only"]';
  const homePath = '/';
  const toggleEventName = 'astro:day-dev-indicator-toggle-request';
  let routeEligibilityFrame = null;

  const findBadge = () => {
    const badge = document.querySelector(badgeSelector);
    return badge instanceof HTMLButtonElement ? badge : null;
  };

  const applyRouteEligibility = () => {
    if (routeEligibilityFrame !== null) {
      window.cancelAnimationFrame(routeEligibilityFrame);
      routeEligibilityFrame = null;
    }
    const badge = findBadge();
    if (!badge) return false;
    const isHomeRoute = window.location.pathname === homePath;
    badge.dataset.routeEligible = String(isHomeRoute);
    badge.tabIndex = isHomeRoute ? 0 : -1;
    badge.setAttribute('aria-disabled', String(!isHomeRoute));
    badge.classList.toggle('pointer-events-none', !isHomeRoute);
    badge.classList.toggle('cursor-default', !isHomeRoute);
    badge.classList.toggle('cursor-pointer', isHomeRoute);
    return true;
  };

  const syncRouteEligibility = () => {
    if (applyRouteEligibility()) return;
    routeEligibilityFrame = window.requestAnimationFrame(() => {
      routeEligibilityFrame = null;
      applyRouteEligibility();
    });
  };

  const handleClick = (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const badge = target.closest(badgeSelector);
    if (!(badge instanceof HTMLButtonElement)) return;
    if (window.location.pathname !== homePath) {
      event.preventDefault();
      syncRouteEligibility();
      return;
    }
    syncRouteEligibility();
    window.dispatchEvent(new CustomEvent(toggleEventName, {
      detail: { route: homePath, source: 'layout-runtime-badge' },
    }));
  };

  const wrapHistoryMethod = (method) => {
    const original = window.history[method].bind(window.history);
    const wrapped = (...args) => {
      const result = original(...args);
      syncRouteEligibility();
      return result;
    };
    window.history[method] = wrapped;
    return () => {
      window.history[method] = original;
    };
  };

  const restorePushState = wrapHistoryMethod('pushState');
  const restoreReplaceState = wrapHistoryMethod('replaceState');

  document.addEventListener('click', handleClick);
  window.addEventListener('popstate', syncRouteEligibility);
  window.addEventListener('hashchange', syncRouteEligibility);
  document.addEventListener('DOMContentLoaded', syncRouteEligibility);
  syncRouteEligibility();

  win.__ASTRO_RUNTIME_BADGE_ROUTE_GATE__ = {
    dispose: () => {
      if (routeEligibilityFrame !== null) {
        window.cancelAnimationFrame(routeEligibilityFrame);
        routeEligibilityFrame = null;
      }
      restorePushState();
      restoreReplaceState();
      document.removeEventListener('click', handleClick);
      window.removeEventListener('popstate', syncRouteEligibility);
      window.removeEventListener('hashchange', syncRouteEligibility);
      document.removeEventListener('DOMContentLoaded', syncRouteEligibility);
    },
  };
})();
`;

const runtimeEnvironment =
  process.env.ENVIRONMENT ||
  process.env.NEXT_PUBLIC_ENVIRONMENT ||
  process.env.VERCEL_ENV ||
  process.env.NODE_ENV;

const isProductionRuntime =
  runtimeEnvironment && runtimeEnvironment.toLowerCase() === 'production';

const environmentBadgeLabel = isProductionRuntime ? 'PROD' : 'DEV';

function RuntimeEnvironmentBadge() {
  const sharedClassName = "fixed right-2 top-2 z-50 rounded bg-black/55 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-white/85 select-none";

  if (isProductionRuntime) {
    return (
      <div data-testid="runtime-environment-badge" className={`${sharedClassName} pointer-events-none`}>
        {environmentBadgeLabel}
      </div>
    );
  }

  return (
    <>
      <Script id="runtime-badge-route-gate" strategy="beforeInteractive">
        {DEV_RUNTIME_BADGE_ROUTE_GATE}
      </Script>
      <button
        type="button"
        data-testid="runtime-environment-badge"
        data-runtime-badge-route-gate="day-home-only"
        data-runtime-badge-event="astro:day-dev-indicator-toggle-request"
        data-route-eligible="false"
        aria-disabled="true"
        tabIndex={-1}
        className={`${sharedClassName} pointer-events-none cursor-default`}
      >
        {environmentBadgeLabel}
      </button>
    </>
  );
}

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
        <RuntimeEnvironmentBadge />
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
