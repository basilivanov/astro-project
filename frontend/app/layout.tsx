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
        <main className="min-h-screen relative z-10">
            {children}
        </main>
        <BottomNav />
      </body>
    </html>
  );
}
// #END_BLOCK_LAYOUT_ROOT
