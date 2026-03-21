import { Loader2, AlertCircle, FileX } from "lucide-react";
import Link from "next/link";
import { cn } from "../lib/utils";

type BaseStateProps = {
  compact?: boolean;
  className?: string;
};

export function LoadingState({
  message = "Связываемся со звездами...",
  compact = false,
  className,
}: {
  message?: string;
} & BaseStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center animate-in fade-in duration-500",
        compact ? "min-h-0 px-4 py-6" : "min-h-[60vh] p-6",
        className,
      )}
    >
      <div className="relative">
        <div className="absolute inset-0 bg-purple-500/20 blur-xl rounded-full animate-pulse"></div>
        <Loader2 className="relative w-12 h-12 text-purple-600 animate-spin mb-4" />
      </div>
      <p className="text-slate-500 text-sm font-medium">{message}</p>
    </div>
  );
}

export function ErrorState({
  error,
  onRetry,
  compact = false,
  className,
}: {
  error: string;
  onRetry?: () => void;
} & BaseStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center animate-in zoom-in-95 duration-300",
        compact ? "min-h-0 px-4 py-2" : "min-h-[60vh] p-6",
        className,
      )}
    >
      <div className="w-16 h-16 bg-rose-50 text-rose-500 rounded-full flex items-center justify-center mb-4 shadow-sm border border-rose-100">
        <AlertCircle size={32} />
      </div>
      <h3 className="text-lg font-bold text-slate-900 mb-2">Упс, ошибка</h3>
      <p className="text-slate-500 text-sm mb-6 max-w-xs leading-relaxed">{error}</p>
      {onRetry && (
        <button 
            onClick={onRetry} 
            className="px-6 py-3 rounded-xl bg-slate-900 text-white font-bold text-sm hover:opacity-90 transition-opacity active:scale-95"
        >
            Попробовать снова
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  title = "Здесь пока пусто",
  message,
  actionLabel,
  actionHref,
  onActionClick,
  actionTestId,
  compact = false,
  className,
}: {
  title?: string;
  message: string;
  actionLabel?: string;
  actionHref?: string;
  onActionClick?: () => void;
  actionTestId?: string;
} & BaseStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center border border-dashed border-slate-200 rounded-3xl bg-slate-50/50",
        compact ? "py-8 px-4" : "py-12 px-6",
        className,
      )}
    >
      <div className="w-14 h-14 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mb-4">
        <FileX size={24} />
      </div>
      <h3 className="text-base font-bold text-slate-800 mb-1">{title}</h3>
      <p className="text-slate-500 text-xs mb-6 max-w-[260px] leading-relaxed">{message}</p>
      {actionLabel && actionHref && (
        <Link
          href={actionHref}
          onClick={onActionClick}
          data-testid={actionTestId}
          className="text-purple-600 font-bold text-sm hover:underline"
        >
          {actionLabel} →
        </Link>
      )}
    </div>
  );
}
