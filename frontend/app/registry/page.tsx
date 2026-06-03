"use client"

import { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import { getSets } from "@/lib/api";
import { SetSummary } from "@/types/api";
import debounce from "lodash/debounce";
import { Search } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export default function SetsPage() {
  const [data, setData] = useState<SetSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [query, setQuery] = useState<string>("");

  useEffect(() => {
    setIsLoading(true);
    getSets()
      .then((res) => setData(res.items))
      .finally(() => setIsLoading(false));
  }, []);

  const handleUpdateQuery = useCallback(
    debounce((value: string) => setQuery(value), 300),
    []
  );

  const setsBySeries = useMemo(() => {
    if (data.length === 0) return {};
    const filtered = query
      ? data.filter((s) => s.name.toLowerCase().includes(query.toLowerCase()))
      : data;
    const res: Record<string, SetSummary[]> = {};
    for (const s of filtered) {
      (res[s.series] ??= []).push(s);
    }
    return res;
  }, [data, query]);

  const seriesEntries = Object.entries(setsBySeries);

  return (
    <div className="space-y-10">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <h1 className="font-display text-[26px] font-bold text-fg-1">Set Registry</h1>
        <div className="relative w-[260px]">
          <Search size={14} strokeWidth={1.5} className="absolute left-3 top-1/2 -translate-y-1/2 text-fg-3 pointer-events-none" />
          <input
            onChange={(e) => handleUpdateQuery(e.target.value)}
            className="w-full h-9 pl-9 pr-3 rounded-full bg-surface border border-border text-[13px] text-fg-1 placeholder:text-fg-4 outline-none focus:ring-1 focus:ring-white/20"
            placeholder="Search sets…"
          />
        </div>
      </div>

      {/* Body */}
      {isLoading ? (
        <div className="space-y-10">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i}>
              <div className="flex items-center gap-3 mb-5">
                <div className="h-3 w-24 rounded bg-surface animate-pulse" />
                <div className="h-px flex-1 bg-border" />
              </div>
              <ul className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                {Array.from({ length: 5 }).map((_, j) => (
                  <li key={j} className="h-[120px] rounded-xl bg-surface border border-border animate-pulse" />
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : seriesEntries.length === 0 ? (
        <p className="text-center text-fg-3 py-16">No sets found.</p>
      ) : (
        <div className="space-y-10">
          {seriesEntries.map(([seriesName, sets]) => (
            <div key={seriesName}>
              {/* Series heading with rule */}
              <div className="flex items-center gap-3 mb-5">
                <h2 className="font-display text-[15px] font-semibold text-fg-2 shrink-0 uppercase tracking-wide">
                  {seriesName}
                </h2>
                <div className="h-px flex-1 bg-border" />
              </div>

              <ul className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                {sets.map((s) => (
                  <li key={`${s.name}_${s.set_id}`}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link href={`/registry/cards?set_id=${s.set_id}`} className="no-underline">
                          <div className="flex flex-col items-center justify-center p-5 h-[120px] rounded-xl bg-surface border border-border hover:border-border-2 hover:bg-elevated transition-all cursor-pointer">
                            {s.image_logo ? (
                              <img
                                src={s.image_logo}
                                alt={s.name}
                                className="max-h-[52px] max-w-[120px] object-contain"
                              />
                            ) : (
                              <span className="text-[13px] font-semibold text-fg-2 text-center leading-snug">
                                {s.name}
                              </span>
                            )}
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>{s.name}</TooltipContent>
                    </Tooltip>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
