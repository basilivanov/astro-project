import React from "react";

// START_BLOCK_DIVIDER_BLOCK
export const DividerBlock: React.FC = () => {
  return (
    <div className="flex items-center justify-center py-2 opacity-40">
        <div className="h-px bg-slate-300 w-full max-w-[100px]"></div>
        <span className="mx-2 text-slate-400">✦</span>
        <div className="h-px bg-slate-300 w-full max-w-[100px]"></div>
    </div>
  );
};
// END_BLOCK_DIVIDER_BLOCK
