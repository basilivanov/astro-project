import { Suspense } from "react";

import BillingCompletePageClient from "./billing-complete-page-client";

export const dynamic = "force-dynamic";

function BillingCompleteFallback() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-6 text-center">
      <div className="max-w-sm rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold text-slate-800">Возвращаем вас к оформлению</p>
        <p className="mt-2 text-sm leading-relaxed text-slate-500">
          Проверяем платежную сессию и подхватываем ваш разовый unlock.
        </p>
      </div>
    </div>
  );
}

export default function BillingCompletePage() {
  return (
    <Suspense fallback={<BillingCompleteFallback />}>
      <BillingCompletePageClient />
    </Suspense>
  );
}
