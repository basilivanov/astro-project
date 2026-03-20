// ############################################################################
// AI_HEADER: MODULE_ADMIN_SEARCH
// ROLE: Debounced search input for admin dashboard.
// DEPENDENCIES: next/navigation.
// GRACE_ANCHORS: [ADMIN_SEARCH]
// ############################################################################

"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useDebouncedCallback } from "use-debounce";
import { Loader2 } from "lucide-react";
import { useState, useTransition } from "react";

export default function AdminSearch({ placeholder }: { placeholder: string }) {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const { replace } = useRouter();
  const [isPending, startTransition] = useTransition();
  const [term, setTerm] = useState(searchParams.get("q")?.toString() || "");

  const handleSearch = useDebouncedCallback((value: string) => {
    startTransition(() => {
      const params = new URLSearchParams(searchParams);
      if (value) {
        params.set("q", value);
      } else {
        params.delete("q");
      }
      replace(`${pathname}?${params.toString()}`);
    });
  }, 300);

  return (
    <div className="relative flex flex-1 flex-shrink-0">
      <input
        className="input py-1 px-3 text-sm w-full sm:w-60"
        placeholder={placeholder}
        defaultValue={searchParams.get("q")?.toString()}
        onChange={(e) => {
          setTerm(e.target.value);
          handleSearch(e.target.value);
        }}
      />
      {isPending && (
        <div className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500">
          <Loader2 size={14} className="animate-spin" />
        </div>
      )}
    </div>
  );
}
