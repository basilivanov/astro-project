"use client";

import { useEffect, useState } from 'react';

export function useTelegram() {
  const [user, setUser] = useState<any>(null);
  const [webApp, setWebApp] = useState<any>(null);
  const [initData, setInitData] = useState<string>("");
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const isMock = params.get("mock") === "1";
      const isGuest = params.get("guest") === "1";
      
      // 1. Guest Mode override
      if (isGuest) {
        setUser(null);
        setInitData("");
        sessionStorage.removeItem("mock_telegram_user");
        setIsReady(true);
        return;
      }

      // 2. Telegram WebApp Check
      const tg = (window as any).Telegram?.WebApp;
      if (tg && tg.initData) {
        console.log("[useTelegram] Running in Telegram");
        tg.ready();
        setWebApp(tg);
        setInitData(tg.initData);
        try { tg.expand(); } catch (e) {}
        setUser(tg.initDataUnsafe?.user || null);
        setIsReady(true);
        return;
      }

      // 3. Mock / Browser Mode
      const storedMock = sessionStorage.getItem("mock_telegram_user");
      
      if (isMock || storedMock) {
        console.log("[useTelegram] Using Mock User");
        const mockUser = { 
            id: 123456789, 
            first_name: "Dev User", 
            username: "dev_user",
            language_code: "ru",
            photo_url: ""
        };
        
        // Persist
        if (isMock) {
            sessionStorage.setItem("mock_telegram_user", "1");
        }
        
        setInitData("123456789"); // Matches backend DEV_BYPASS format
        setUser(mockUser);
      } else {
        console.log("[useTelegram] No auth found");
      }
      
      setIsReady(true);
    }
  }, []);

  const onClose = () => {
    webApp?.close();
  };

  return { user, webApp, initData, isReady, onClose };
}
