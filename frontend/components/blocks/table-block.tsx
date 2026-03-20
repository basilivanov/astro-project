import React from "react";
import { cn } from "../../lib/utils";

// ############################################################################
// AI_HEADER: MODULE_BLOCK_TABLE
// ROLE: Mobile-first responsive table component.
// CONTEXT: Renders rows as cards on small screens to avoid horizontal scroll.
// ############################################################################

interface TableColumn {
  header: string;
  accessorKey?: string;
  width?: string;
  align?: "left" | "center" | "right";
  nowrap?: boolean;
}

interface TableBlockProps {
  columns: TableColumn[];
  rows: any[][];
  className?: string;
}

export const TableBlock: React.FC<TableBlockProps> = ({ columns, rows, className }) => {
  if (!rows || rows.length === 0) return null;

  return (
    <div className={cn("w-full overflow-hidden", className)} data-testid="report-table">
      {/* Desktop Table View (Tablet and up) */}
      <div className="hidden sm:block overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <colgroup>
              {columns.map((col, idx) => (
                <col key={idx} style={{ width: col.width || 'auto' }} />
              ))}
            </colgroup>
            
            <thead className="bg-slate-50/80 text-slate-500 font-bold uppercase text-[10px] tracking-widest border-b border-slate-200">
              <tr>
                {columns.map((col, idx) => (
                  <th 
                    key={idx} 
                    className={cn(
                      "px-4 py-3.5", 
                      col.align === "center" && "text-center",
                      col.align === "right" && "text-right",
                      col.nowrap && "whitespace-nowrap"
                    )}
                  >
                    {col.header}
                  </th>
                ))}
              </tr>
            </thead>
            
            <tbody className="divide-y divide-slate-100 bg-white">
              {rows.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-slate-50/50 transition-colors group">
                  {row.map((cell, cIdx) => {
                    const col = columns[cIdx];
                    const isNumeric = col?.align === "right" || col?.align === "center";
                    
                    return (
                      <td 
                        key={cIdx} 
                        className={cn(
                          "px-4 py-3 text-slate-700 align-middle leading-[1.5]",
                          col?.align === "center" && "text-center",
                          col?.align === "right" && "text-right",
                          col?.nowrap ? "whitespace-nowrap" : "break-words",
                          isNumeric && "tabular-nums font-feature-settings-tnum font-medium text-slate-900"
                        )}
                      >
                        {cell}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mobile Card View (Stack layout) */}
      <div className="sm:hidden space-y-3">
        {rows.map((row, rIdx) => (
          <div key={rIdx} className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-2 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-slate-100 group-active:bg-purple-200 transition-colors" />
            {columns.map((col, cIdx) => (
              <div key={cIdx} className="flex justify-between items-baseline gap-4">
                <span className="text-slate-400 text-[10px] font-bold uppercase tracking-widest shrink-0">
                  {col.header}
                </span>
                <span className={cn(
                  "text-slate-800 text-sm font-semibold text-right break-words min-w-0 flex-1",
                  (col?.align === "right" || col?.align === "center") && "tabular-nums font-feature-settings-tnum text-purple-700"
                )}>
                  {row[cIdx]}
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};