import React from "react";
import { cn } from "../../lib/utils";
import { AlertCircle, CheckCircle2, Info, XCircle } from "lucide-react";

export type CalloutType = "info" | "success" | "warning" | "error" | "neutral";

interface CalloutBlockProps {
  type?: CalloutType;
  title?: string;
  children: React.ReactNode;
  className?: string;
}

const icons = {
  info: Info,
  success: CheckCircle2,
  warning: AlertCircle,
  error: XCircle,
  neutral: Info,
};

const styles = {
  info: "bg-blue-50 border-blue-200 text-blue-900",
  success: "bg-green-50 border-green-200 text-green-900",
  warning: "bg-amber-50 border-amber-200 text-amber-900",
  error: "bg-rose-50 border-rose-200 text-rose-900",
  neutral: "bg-slate-50 border-slate-200 text-slate-900",
};

export const CalloutBlock: React.FC<CalloutBlockProps> = ({ 
  type = "neutral", 
  title, 
  children, 
  className 
}) => {
  const Icon = icons[type] || icons.neutral;
  
  return (
    <div className={cn("p-3 rounded-lg border flex gap-3 text-sm", styles[type] || styles.neutral, className)}>
      <Icon className="w-5 h-5 flex-shrink-0 mt-0.5 opacity-80" />
      <div className="flex-1 space-y-1">
        {title && <h4 className="font-semibold">{title}</h4>}
        <div className="opacity-90 leading-relaxed overflow-wrap-anywhere">
            {children}
        </div>
      </div>
    </div>
  );
};
