// ############################################################################
// AI_HEADER: MODULE_BILLING_COMPLETE_PAGE
// ROLE: Resume the create flow after provider redirect using persisted checkout session.
// DEPENDENCIES: useTelegram, api/billing/sessions/{resume_token}.
// ############################################################################

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";

import { useTelegram } from "../../../hooks/useTelegram";

function appendQueryParam(path: string, key: string, value: string): string {
  const glue = path.includes("?") ? "&" : "?";
  return `${path}${glue}${key}=${encodeURIComponent(value)}`;
}

export default function BillingCompletePageClient() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { initData, isReady, mode } = useTelegram();

  const checkoutToken = searchParams.get("checkout");
  const mockEnabled = searchParams.get("mock") === "1";
  const runtimeEnabled = searchParams.get("runtime") === "1";
  const statusOverride = searchParams.get("status");
  const reasonOverride = searchParams.get("reason");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState(
    "Проверяем платежную сессию и подхватываем ваш разовый unlock.",
  );
  const [swipeBackHintVisible, setSwipeBackHintVisible] = useState(false);
  const touchStartX = useRef<number | null>(null);

  const fallbackHref = useMemo(() => {
    const params = new URLSearchParams();
    if (mockEnabled || mode === "mock") {
      params.set("mock", "1");
    }
    if (runtimeEnabled || mockEnabled || mode === "mock") {
      params.set("runtime", "1");
    }
    const query = params.toString();
    return query ? `/reports?${query}` : "/reports";
  }, [mockEnabled, mode, runtimeEnabled]);

  useEffect(() => {
    if (!statusOverride) {
      return;
    }
    if (statusOverride === "failed") {
      if (reasonOverride === "provider_return_failed") {
        setError("ЮMoney вернул оплату с ошибкой. Проверьте статус платежа и попробуйте снова.");
      } else {
        setError("Платежная сессия завершилась с ошибкой. Попробуйте снова.");
      }
    }
    if (statusOverride === "canceled") {
      setError("Оплата была отменена. Вернитесь к оформлению и попробуйте снова.");
    }
  }, [reasonOverride, statusOverride]);

  useEffect(() => {
    const handleTouchStart = (event: TouchEvent) => {
      touchStartX.current = event.changedTouches[0]?.clientX ?? null;
    };

    const handleTouchEnd = (event: TouchEvent) => {
      const startX = touchStartX.current;
      const endX = event.changedTouches[0]?.clientX ?? null;
      touchStartX.current = null;
      if (startX === null || endX === null) {
        return;
      }
      if (endX - startX < 72) {
        return;
      }
      setSwipeBackHintVisible(true);
      router.push(fallbackHref);
    };

    window.addEventListener("touchstart", handleTouchStart, { passive: true });
    window.addEventListener("touchend", handleTouchEnd, { passive: true });
    return () => {
      window.removeEventListener("touchstart", handleTouchStart);
      window.removeEventListener("touchend", handleTouchEnd);
    };
  }, [fallbackHref, router]);

  useEffect(() => {
    if (error) {
      return;
    }
    if (!isReady) {
      return;
    }

    if (!checkoutToken) {
      setError("Checkout token не найден.");
      return;
    }

    if (!initData) {
      setError("Нужен возврат в Telegram WebApp, чтобы продолжить оформление.");
      return;
    }

    let cancelled = false;
    let timeoutId: number | undefined;

    const resumeCheckout = async () => {
      try {
        const response = await fetch(`/api/billing/sessions/${checkoutToken}`, {
          headers: { "X-Telegram-Auth": initData },
        });

        if (!response.ok) {
          throw new Error("checkout_session_unavailable");
        }

        const session = (await response.json()) as {
          status?: string;
          resumed_report_id?: string | null;
          return_path?: string | null;
          report_type?: string | null;
        };

        if (cancelled) {
          return;
        }

        if (session.resumed_report_id) {
          let readPath = `/read/${session.resumed_report_id}`;
          if (mockEnabled || mode === "mock") {
            readPath = appendQueryParam(readPath, "mock", "1");
          }
          router.replace(readPath);
          return;
        }

        if (session.status === "pending" || session.status === "created") {
          setMessage("Ждем подтверждения оплаты. Как только провайдер подтвердит платеж, продолжим автоматически.");
          timeoutId = window.setTimeout(() => {
            void resumeCheckout();
          }, 1500);
          return;
        }

        if (session.status === "succeeded" || session.status === "resumed") {
          setMessage("Оплата подтверждена. Возвращаем вас к созданию разбора и завершаем запуск автоматически.");
        }

        if (session.status === "canceled") {
          setError("Оплата была отменена. Вернитесь к оформлению и попробуйте снова.");
          return;
        }

        if (session.status === "failed") {
          setError("Платежная сессия завершилась с ошибкой. Попробуйте снова.");
          return;
        }

        let targetPath =
          session.return_path || (session.report_type ? `/create?type=${session.report_type}` : "/reports");
        targetPath = appendQueryParam(targetPath, "checkout", checkoutToken);

        if (mockEnabled || mode === "mock") {
          targetPath = appendQueryParam(targetPath, "mock", "1");
        }
        if (runtimeEnabled || mockEnabled || mode === "mock") {
          targetPath = appendQueryParam(targetPath, "runtime", "1");
        }

        router.replace(targetPath);
      } catch (resumeError) {
        console.error(resumeError);
        if (!cancelled) {
          setError("Не удалось восстановить платежную сессию.");
        }
      }
    };

    void resumeCheckout();

    return () => {
      cancelled = true;
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [checkoutToken, error, initData, isReady, mockEnabled, mode, router, runtimeEnabled]);

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-6 text-center">
        <div className="max-w-sm rounded-3xl border border-rose-100 bg-white p-6 shadow-sm">
          <button
            type="button"
            onClick={() => router.push(fallbackHref)}
            className="mb-4 inline-flex items-center gap-2 rounded-2xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700"
          >
            <ArrowLeft size={16} /> Назад
          </button>
          <p className="text-sm font-semibold text-slate-800">{error}</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-500">
            Вернитесь к оформлению и попробуйте снова.
          </p>
          <button
            type="button"
            data-testid="billing-complete-swipe-back"
            onClick={() => {
              setSwipeBackHintVisible(true);
              router.push(fallbackHref);
            }}
            className="mt-3 inline-flex rounded-2xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600"
          >
            Смахнуть назад
          </button>
          {swipeBackHintVisible ? (
            <p className="mt-2 text-xs text-slate-400">Жест назад обработан.</p>
          ) : null}
          <Link
            href={fallbackHref}
            className="mt-5 inline-flex rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white"
          >
            К каталогу
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-6 text-center">
      <div className="max-w-sm rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <button
          type="button"
          onClick={() => router.push(fallbackHref)}
          className="mb-4 inline-flex items-center gap-2 rounded-2xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700"
        >
          <ArrowLeft size={16} /> Назад
        </button>
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
          <Loader2 className="animate-spin" size={24} />
        </div>
        <p className="mt-4 text-sm font-semibold text-slate-800">Возвращаем вас к оформлению</p>
        <p className="mt-2 text-sm leading-relaxed text-slate-500">{message}</p>
      </div>
    </div>
  );
}
