import { useState, useCallback, useEffect, useRef } from "react";
import {
  Dialog,
  DialogTrigger,
  DialogPortal,
  DialogClose,
  DialogContent,
  DialogOverlay,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { VisuallyHidden } from "radix-ui";
import { MagnifyingGlassIcon } from "@radix-ui/react-icons";
import debounce from "lodash/debounce";
import { algoliaClient, CARDS_INDEX } from "@/lib/algolia";
import { CardIndex } from "@/types/api";
import { capitalizeStr } from "@/lib/utils";
import Link from "next/link";

const HITS_PER_PAGE = 10;

export default function SearchDialog() {
  const [query, setQuery] = useState<string>("");
  const [searchResults, setSearchResults] = useState<CardIndex[]>([]);
  const [isOpened, setIsOpened] = useState<boolean>(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const handleUpdateQuery = useCallback(
    debounce((value: string) => setQuery(value), 500),
    []
  );

  // Fetch a page of results. append=true adds to existing list, false replaces.
  const fetchPage = useCallback(async (searchQuery: string, pageNum: number, append: boolean) => {
    const res = await algoliaClient.searchSingleIndex<CardIndex>({
      indexName: CARDS_INDEX,
      searchParams: { query: searchQuery, page: pageNum, hitsPerPage: HITS_PER_PAGE },
    });
    setSearchResults(prev => append ? [...prev, ...res.hits] : res.hits);
    setPage(pageNum);
    setHasMore(pageNum < (res.nbPages ?? 1) - 1);
  }, []);

  // When query changes, reset and fetch page 0
  useEffect(() => {
    if (!query) {
      setSearchResults([]);
      setPage(0);
      setHasMore(false);
      return;
    }
    fetchPage(query, 0, false);
  }, [query]);

  // When dialog closes, reset everything
  useEffect(() => {
    if (!isOpened) {
      setQuery("");
      setSearchResults([]);
      setPage(0);
      setHasMore(false);
    }
  }, [isOpened]);

  // Observe the sentinel — when it enters the viewport, load the next page
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
    <Dialog>
      <DialogTrigger asChild>
        <Button className="text-stone-400" onClick={() => setIsOpened(true)}>
          <div className="flex gap-2 items-center cursor-pointer">
            <MagnifyingGlassIcon width={12} height={12} />
            Search
          </div>
        </Button>
      </DialogTrigger>
      <DialogPortal>
        <DialogContent
          className="bg-slate-800 p-0 rounded-lg w-[450px] md:w-[600px] lg:w-[800px] sm:max-w-none gap-0 top-[15%] translate-y-0"
          showCloseButton={false}
        >
          <VisuallyHidden.Root><DialogTitle></DialogTitle></VisuallyHidden.Root>
          <div className="w-full">
            {/* Input */}
            <div className="flex border-b-[0.5px] border-stone-600">
              <div className="pl-4 flex items-center justify-center">
                <MagnifyingGlassIcon width={16} height={16} className="text-stone-400"/>
              </div>
              <Input
                className="w-full h-12 rounded-none bg-transparent outline-none text-white focus-visible:ring-0 focus-visible:border-transparent"
                placeholder="e.g. Charizard Phantasmal Flames"
                onChange={(e) => handleUpdateQuery(e.target.value)}
              />
            </div>
          </div>
          <div className="py-6 max-h-[400px] md:max-h-[600px] overflow-auto">
            {query.length > 0 ? (
              <ul className="flex flex-col gap-4">
                {searchResults.map((hit) => (
                  <DialogClose asChild key={`${hit.card_id}_${hit.variant}`} onClick={() => setIsOpened(false)}>
                    <Link href={`/cards/${hit.card_id}?variant=${hit.variant}`}>
                      <li className="flex items-center gap-4 list-none cursor-pointer border-b border-stone-700/50 last:border-b-0 hover:bg-slate-700/50 rounded px-12 py-4 transition-colors">
                        <img src={hit.image_small} className="w-[80px] h-[100px] rounded shrink-0"/>
                        <div className="flex flex-col gap-1">
                          <span className="text-white font-bold text-lg">{`${hit.name} (${capitalizeStr(hit.variant)})`}</span>
                          <span className="text-stone-400 text-md">{hit.rarity}</span>
                          <span className="text-stone-400 text-md">{hit.set_name}</span>
                        </div>
                      </li>
                    </Link>
                  </DialogClose>
                ))}
                {/* Sentinel: invisible div that triggers next page load when scrolled into view */}
                <div ref={sentinelRef} className="h-1" />
              </ul>
            ) : (
              <p className="text-md text-stone-300 text-center">No active search.</p>
            )}
          </div>
        </DialogContent>
      </DialogPortal>
    </Dialog>
  )
}
