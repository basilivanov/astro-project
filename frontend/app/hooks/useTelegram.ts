"use client";

import { useEffect, useState } from 'react';

export function useTelegram() {
  const [user, setUser] = useState<any>(null);
  const [webApp, setWebApp] = useState<any>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Check if Telegram WebApp script is loaded
      const tg = (window as any).Telegram?.WebApp;
      if (tg) {
        tg.ready();
        setWebApp(tg);
        tg.expand(); // Expand to full height

        if (tg.initDataUnsafe?.user) {
          setUser(tg.initDataUnsafe.user);
        } else {
            // Development Mock
            console.log("Telegram WebApp not detected or no user data. Using Mock.");
            setUser({ 
                id: 123456789, 
                first_name: "Astro User", 
                username: "dev_user",
                is_premium: true 
            });
        }
        setIsReady(true);
      } else {
         // Fallback for browser
         setUser({ 
            id: 123456789, 
            first_name: "Browser User", 
            username: "browser_dev" 
         });
         setIsReady(true);
      }
    }
  }, []);

  const onClose = () => {
    webApp?.close();
  };

  return { user, webApp, isReady, onClose };
}
