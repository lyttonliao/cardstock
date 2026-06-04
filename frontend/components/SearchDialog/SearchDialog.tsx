import { useState, useCallback, useEffect, useRef } from "react";
import {
  Dialog,
  DialogTrigger,
  DialogPortal,
  DialogContent,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { VisuallyHidden } from "radix-ui";
import { Search } from "lucide-react";
import debounce from "lodash/debounce";
import { algoliaClient, CARDS_INDEX } from "@/lib/algolia";
import { CardIndex } from "@/types/api";
import { capitalizeStr } from "@/lib/format";
import Link from "next/link";
import { DialogClose } from "@radix-ui/react-dialog";

const HITS_PER_PAGE = 10;

export default function SearchDialog() {
  const [query, setQuery] = useState<string>("");
  const [searchResults, setSearchResults] = useState<CardIndex[]>([]);
  const [isOpened, setIsOpened] = useState<boolean>(false);
  const [page, setPage] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  // ⌘K / Ctrl+K shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpened(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const handleUpdateQuery = useCallback(
    debounce((value: string) => setQuery(value), 500),
    []
  );

  const fetchPage = useCallback(async (searchQuery: string, pageNum: number, append: boolean) => {
    setIsLoading(true);
    if (append) await new Promise(resolve => setTimeout(resolve, 1500));
    const res = await algoliaClient.searchSingleIndex<CardIndex>({
      indexName: CARDS_INDEX,
      searchParams: { query: searchQuery, page: pageNum, hitsPerPage: HITS_PER_PAGE },
    });
    setSearchResults(prev => {
      if (!append) return res.hits;
      const seen = new Set(prev.map(h => `${h.card_id}_${h.variant}`));
      return [...prev, ...res.hits.filter(h => !seen.has(`${h.card_id}_${h.variant}`))];
    });
    setPage(pageNum);
    setHasMore(pageNum < (res.nbPages ?? 1) - 1);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (!query) {
      setSearchResults([]);
      setPage(0);
      setHasMore(false);
      return;
    }
    fetchPage(query, 0, false);
  }, [query]);

  useEffect(() => {
    if (!isOpened) {
      setQuery("");
      setSearchResults([]);
      setPage(0);
      setHasMore(false);
    }
  }, [isOpened]);

  useEffect(() => {
    if (!sentinelRef.current) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && hasMore) {
        fetchPage(query, page + 1, true);
      }
    });
    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [hasMore, page, query, fetchPage]);

  return (
    <Dialog open={isOpened} onOpenChange={setIsOpened}>
      {/* Trigger — ghost button with ⌘K hint */}
      <DialogTrigger asChild>
        <button className="inline-flex items-center gap-1.5 h-9 px-[14px] rounded-full text-fg-2 text-[13px] font-medium hover:bg-hover hover:text-fg-1 transition-colors cursor-pointer">
          <Search size={14} strokeWidth={1.5} />
          Search
          <kbd className="font-mono text-[10px] px-1.5 py-0.5 rounded-[6px] bg-white/[0.12] text-fg-3 ml-1">⌘K</kbd>
        </button>
      </DialogTrigger>

      <DialogPortal>
        <DialogContent
          className="bg-elevated rounded-[24px] border border-border p-0 shadow-[0_25px_50px_-12px_rgba(0,0,0,0.5)] top-4 md:top-[15%] translate-y-0 flex flex-col"
          aria-describedby={undefined}
          showCloseButton={false}
        >
          <VisuallyHidden.Root><DialogTitle /></VisuallyHidden.Root>

          {/* Input row */}
          <div className="flex items-center gap-3 px-[18px] h-14 border-b border-border shrink-0">
            <Search size={16} strokeWidth={1.5} className="text-fg-3 shrink-0" />
            <input
              autoFocus
              placeholder="e.g. Charizard Phantasmal Flames"
              onChange={(e) => handleUpdateQuery(e.target.value)}
              className="flex-1 bg-transparent border-none outline-none text-fg-1 text-[15px] font-[inherit] placeholder:text-fg-4"
            />
            <kbd className="font-mono text-[11px] px-2 py-0.5 rounded-[6px] bg-white/[0.12] text-fg-3 shrink-0">Esc</kbd>
          </div>

          {/* Results */}
          <div className="py-3 overflow-y-auto md:max-h-[520px]">
            {searchResults.length > 0 ? (
              <ul className="list-none p-0 m-0 flex flex-col gap-0.5">
                {searchResults.map((hit) => (
                  <DialogClose asChild key={`${hit.card_id}_${hit.variant}`}>
                    <Link href={`/registry/cards/${hit.card_id}?variant=${hit.variant}`} className="no-underline">
                      <li className="flex items-center gap-4 px-12 py-3 rounded-lg cursor-pointer hover:bg-[rgba(51,65,85,0.5)] transition-colors">
                        <div className="w-14 h-[76px] rounded-md bg-surface border border-border shrink-0 overflow-hidden">
                          <img src={hit.image_small} alt="" className="w-full h-full object-cover block" />
                        </div>
                        <div className="flex flex-col gap-[3px]">
                          <span className="text-[15px] font-bold text-fg-1">
                            {hit.name} ({capitalizeStr(hit.variant)})
                          </span>
                          <span className="text-[12px] text-fg-3">{hit.rarity}</span>
                          <span className="text-[12px] text-fg-3">{hit.set_name}</span>
                        </div>
                      </li>
                    </Link>
                  </DialogClose>
                ))}

                {/* Skeleton rows while loading next page */}
                {isLoading && Array.from({ length: 3 }).map((_, i) => (
                  <li key={`skeleton-${i}`} className="flex items-center gap-4 px-12 py-3">
                    <div className="w-14 h-[76px] rounded-md bg-surface shrink-0 animate-pulse" />
                    <div className="flex flex-col gap-1.5 flex-1">
                      <div className="h-3 w-3/5 rounded bg-surface animate-pulse" />
                      <div className="h-2.5 w-2/5 rounded bg-surface animate-pulse" />
                      <div className="h-2.5 w-1/2 rounded bg-surface animate-pulse" />
                    </div>
                  </li>
                ))}

                <div ref={sentinelRef} className="h-px" />
              </ul>
            ) : (
              <p className="text-center text-fg-3 text-[14px] py-6">
                {query ? "No results." : "No active search."}
              </p>
            )}
          </div>
          <DialogFooter className="px-8 py-4 text-end border-t border-border">
            <p className="text-[13px] text-fg-3 font-display">Search by algolia</p>
          </DialogFooter>
        </DialogContent>
      </DialogPortal>
    </Dialog>
  );
}
