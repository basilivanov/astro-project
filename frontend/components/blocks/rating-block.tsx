import React from "react";
import { cn } from "../../lib/utils";

interface RatingBlockProps {
  value: number; // e.g. 8
  max?: number; // e.g. 10
  label?: string; // e.g. "Энергия"
  className?: string;
}

export const RatingBlock: React.FC<RatingBlockProps> = ({ value, max = 10, label, className }) => {
  // Simple color coding based on value
  const percentage = (value / max) * 100;
  let colorClass = "bg-slate-100 text-slate-700"; // default
  
  if (percentage >= 70) colorClass = "bg-green-100 text-green-800";
  else if (percentage >= 40) colorClass = "bg-amber-100 text-amber-800";
  else colorClass = "bg-rose-100 text-rose-800";

  return (
    <div className={cn("inline-flex items-center gap-2 whitespace-nowrap", className)}>
      {label && <span className="font-medium text-slate-700">{label}:</span>}
      <span className={cn("px-2 py-0.5 rounded-md text-sm font-bold font-mono", colorClass)}>
        {value}/{max}
      </span>
    </div>
  );
};
