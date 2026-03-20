import React from "react";
import { cn } from "../../lib/utils";

interface BulletsBlockProps {
  items: React.ReactNode[];
  ordered?: boolean;
  className?: string;
}

export const BulletsBlock: React.FC<BulletsBlockProps> = ({ items, ordered = false, className }) => {
  const Tag = ordered ? "ol" : "ul";
  
  return (
    <Tag className={cn(
      "space-y-2 pl-5 text-slate-700", 
      ordered ? "list-decimal" : "list-disc",
      className
    )}>
      {items.map((item, idx) => (
        <li key={idx} className="pl-1 leading-relaxed overflow-wrap-anywhere">
          {item}
        </li>
      ))}
    </Tag>
  );
};
