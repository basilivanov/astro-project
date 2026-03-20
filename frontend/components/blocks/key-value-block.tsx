import React from "react";
import { cn } from "../../lib/utils";

// START_BLOCK_KEY_VALUE_BLOCK
export interface KeyValueItem {
  key: string;
  value: React.ReactNode;
}

interface KeyValueBlockProps {
  items: KeyValueItem[];
  className?: string;
}

export const KeyValueBlock: React.FC<KeyValueBlockProps> = ({ items, className }) => {
  return (
    <div className={cn("grid grid-cols-[90px_1fr] sm:grid-cols-[160px_1fr] gap-x-3 gap-y-2 text-sm", className)}>
      {items.map((item, idx) => (
        <React.Fragment key={idx}>
          <div className="font-semibold text-slate-500 text-right leading-snug select-none break-words">
            {item.key}:
          </div>
          <div className="text-slate-900 leading-snug overflow-wrap-anywhere tabular-nums min-w-0">
            {item.value}
          </div>
        </React.Fragment>
      ))}
    </div>
  );
};
// END_BLOCK_KEY_VALUE_BLOCK
