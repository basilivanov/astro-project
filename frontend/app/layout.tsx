// ############################################################################
// AI_HEADER: MODULE_LAYOUT
// ROLE: Global layout for the admin UI.
// DEPENDENCIES: globals.css.
// GRACE_ANCHORS: [LAYOUT_ROOT]
// ############################################################################

import "./globals.css";

export const metadata = {
  title: "AstroSaaS Admin",
  description: "Admin dashboard for AstroSaaS MVP",
  icons: {
    icon: "/favicon.svg",
  },
};

// #START_BLOCK_LAYOUT_ROOT
import Script from 'next/script';
import BottomNav from './components/BottomNav';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <Script 
            src="https://telegram.org/js/telegram-web-app.js" 
            strategy="beforeInteractive" 
        />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
      </head>
      <body className="bg-black text-white antialiased pb-24">
        <main className="min-h-screen">
            {children}
        </main>
        <BottomNav />
      </body>
    </html>
  );
}
// #END_BLOCK_LAYOUT_ROOT
