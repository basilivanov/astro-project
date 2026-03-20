"use client";

import { useEffect, useState } from 'react';

type TelegramMode = "telegram" | "mock" | "guest" | "none";

const MOCK_INIT_DATA = "123456789";
const MOCK_USER = {
  id: 123456789,
  first_name: "Debug",
  last_name: "User",
  username: "dev_user",
  language_code: "ru",
  photo_url: ""
};

export function useTelegram() {
  const [user, setUser] = useState<any>(null);
  const [webApp, setWebApp] = useState<any>(null);
  const [initData, setInitData] = useState<string>("");
  const [isReady, setIsReady] = useState(false);
  const [mode, setMode] = useState<TelegramMode>("none");

  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        const params = new URLSearchParams(window.location.search);
        const tg = (window as any).Telegram?.WebApp;
        const hasMockSession = window.sessionStorage.getItem("mock_telegram_user") === "1";
        const hasMockQuery = params.get("mock") === "1";
        const hasMockInitData = tg?.initData === MOCK_INIT_DATA;
        const isMock = hasMockQuery || hasMockSession || hasMockInitData;
        const isGuest = params.get("guest") === "1";

        if (isGuest) {
          setMode("guest");
          return;
        }

        if (isMock) {
          window.sessionStorage.setItem("mock_telegram_user", "1");
          const overrideData = (window as any).MOCK_INIT_DATA_OVERRIDE;
          const overrideUser = (window as any).MOCK_USER_OVERRIDE;
          setUser(overrideUser || MOCK_USER);
          setInitData(overrideData || tg?.initData || MOCK_INIT_DATA);
          setWebApp(tg || null);
          setMode("mock");
          return;
        }

        if (tg && tg.initData) {
          tg.ready();
          setWebApp(tg);
          setInitData(tg.initData);
          setUser(tg.initDataUnsafe?.user || null);
          setMode("telegram");
        } else {
          setMode("none");
        }
      } catch {
        setMode("none");
      } finally {
        setIsReady(true);
      }
    }
  }, []);

  return { user, webApp, initData, isReady, mode, onClose: () => webApp?.close() };
}
