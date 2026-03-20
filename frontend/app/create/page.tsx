import { Suspense } from "react";

import CreatePageClient from "./create-page-client";

export const dynamic = "force-dynamic";

function CreatePageFallback() {
  return (
    <div
      data-testid="create-loading"
      className="flex min-h-screen items-center justify-center bg-slate-50 font-light text-slate-400"
    >
      Загрузка...
    </div>
  );
}

export default function CreatePage() {
  return (
    <Suspense fallback={<CreatePageFallback />}>
      <CreatePageClient />
    </Suspense>
  );
}
