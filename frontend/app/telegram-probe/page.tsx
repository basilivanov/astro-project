"use client";

import { useEffect, useState } from "react";

import { useTelegram } from "../../hooks/useTelegram";

export default function TelegramProbePage() {
  const { user, initData, webApp, isReady, mode, bootstrapOutcome, bootstrapDiagnostics } = useTelegram();
  const [probeResult, setProbeResult] = useState<Record<string, unknown>>({});
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    const onError = (event: ErrorEvent) => setErrors((prev) => [...prev, `error:${event.message}`]);
    const onRejection = (event: PromiseRejectionEvent) => setErrors((prev) => [...prev, `rejection:${String(event.reason)}`]);
    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onRejection);
    return () => {
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onRejection);
    };
  }, []);

  useEffect(() => {
    const run = async () => {
      let usersMeStatus: number | null = null;
      try {
        if (initData) {
          const response = await fetch("/api/users/me", { headers: { "X-Telegram-Auth": initData } });
          usersMeStatus = response.status;
        }
      } catch {
        usersMeStatus = -1;
      }

      let readyCalled = false;
      let expandCalled = false;
      try {
        webApp?.ready?.();
        readyCalled = true;
      } catch {
        readyCalled = false;
      }
      try {
        webApp?.expand?.();
        expandCalled = true;
      } catch {
        expandCalled = false;
      }

      setProbeResult({
        href: window.location.href,
        search: window.location.search,
        hash: window.location.hash,
        telegramPresent: Boolean((window as Window & typeof globalThis & { Telegram?: unknown }).Telegram),
        webAppPresent: Boolean(webApp),
        initDataLength: initData.length,
        userId: user?.id ?? null,
        readyCalled,
        expandCalled,
        usersMeStatus,
      });
    };
    void run();
  }, [initData, user, webApp]);

  return (
    <main className="mx-auto max-w-2xl p-6 space-y-4" data-testid="telegram-probe-page">
      <h1 className="text-2xl font-bold">Telegram Probe</h1>
      <pre data-testid="telegram-probe-bootstrap">{JSON.stringify({ isReady, mode, bootstrapOutcome, bootstrapDiagnostics }, null, 2)}</pre>
      <pre data-testid="telegram-probe-runtime">{JSON.stringify(probeResult, null, 2)}</pre>
      <pre data-testid="telegram-probe-errors">{JSON.stringify(errors, null, 2)}</pre>
    </main>
  );
}
