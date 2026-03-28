// ############################################################################
// AI_HEADER: MODULE_REPORT_STATUS_POLLER
// ROLE: Client-side refresh loop while report is generating.
// DEPENDENCIES: next/navigation.
// GRACE_ANCHORS: [STATUS_REFRESH]
// ############################################################################

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

type ReportStatusPollerProps = {
  reportId: string;
  status: string;
  intervalMs?: number;
};

const ACTIVE_STATUSES = new Set(["in_progress", "pending"]);

export default function ReportStatusPoller({
  reportId,
  status,
  intervalMs = 5000,
}: ReportStatusPollerProps) {
  const router = useRouter();
  const isActive = ACTIVE_STATUSES.has(status);
  const intervalSeconds = Math.max(1, Math.round(intervalMs / 1000));

  useEffect(() => {
    if (!reportId) return;
    if (!isActive) return;

    const handle = window.setInterval(() => {
      router.refresh();
    }, intervalMs);

    return () => window.clearInterval(handle);
  }, [intervalMs, isActive, reportId, router, status]);

  if (!isActive) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 text-xs font-semibold">
      <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500" aria-hidden="true" />
      <span>Собираем неделю… обновляем каждые {intervalSeconds} с.</span>
    </div>
  );
}
