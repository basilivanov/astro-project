import React from "react";
import { cn } from "../../lib/utils";

// START_BLOCK_HEADER_BLOCK
interface HeaderBlockProps {
  level: 1 | 2 | 3 | 4;
  text: string;
  className?: string;
}

export const HeaderBlock: React.FC<HeaderBlockProps> = ({ level, text, className }) => {
  const Tag = `h${level}` as React.ElementType;
  
  const styles = {
    1: "text-xl sm:text-2xl font-bold text-slate-900",
    2: "text-lg sm:text-xl font-bold text-slate-800",
    3: "text-base sm:text-lg font-semibold text-slate-800",
    4: "text-sm sm:text-base font-semibold text-slate-700",
  };

  return <Tag className={cn(styles[level], className)}>{text}</Tag>;
};
// END_BLOCK_HEADER_BLOCK
