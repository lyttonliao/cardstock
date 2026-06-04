"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { getCards } from "@/lib/api";
import { CardSummary } from "@/types/api";
import { capitalizeStr, formatPrice } from "@/lib/format";


const PAGE_SIZE = 20;

export default function CardsPage() {
  return (
    <Suspense>
      <CardsPageContent />
    </Suspense>
  );
}

function CardsPageContent() {
  const searchParams = useSearchParams();
  const setIdParam = searchParams.get("set_id") ?? undefined;

  const [cards, setCards] = useState<CardSummary[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    getCards({ set_id: setIdParam, page: 1, page_size: PAGE_SIZE })
      .then((res) => {
        setCards(res.items);
        setTotal(res.total);
        setPage(1);
        setHasMore(res.items.length < res.total);
      })
      .finally(() => setIsLoading(false));
  }, [setIdParam]);

  function loadMore() {
    const nextPage = page + 1;
    setIsLoadingMore(true);
    getCards({ set_id: setIdParam, page: nextPage, page_size: PAGE_SIZE })
      .then((res) => {
        setCards((prev) => [...prev, ...res.items]);
        setPage(nextPage);
        setHasMore(cards.length + res.items.length < res.total);
      })
      .finally(() => setIsLoadingMore(false));
  }

  return (
    <div>
      {/* Page header */}
      <div className="mb-7">
        <h1 className="font-display text-[32px] font-bold tracking-[-0.025em] text-fg-1 m-0">
          Cards
        </h1>
        {total != null && (
          <p className="text-fg-4 text-[13px] mt-1.5 font-mono">
            {total.toLocaleString()} tracked
          </p>
        )}
      </div>

      {/* Selects */}

      {/* Section header */}
      <div className="flex items-center gap-4 mb-5">
        <span className="text-[11px] tracking-[0.18em] uppercase text-fg-3 font-medium whitespace-nowrap">
          All Cards
        </span>
        <div className="flex-1 h-px bg-border" />
      </div>

      {/* Card list */}
      {isLoading ? (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <SkeletonRow key={i} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {cards.map((card) => (
            <CardRow key={`${card.card_id}_${card.variant}`} card={card} />
          ))}
          {isLoadingMore && Array.from({ length: 4 }).map((_, i) => (
            <SkeletonRow key={`more-${i}`} />
          ))}
        </div>
      )}

      {/* Load more */}
      {hasMore && !isLoading && (
        <div className="flex justify-center mt-8">
          <button
            onClick={loadMore}
            disabled={isLoadingMore}
            className="inline-flex items-center h-9 px-[18px] rounded-full border border-border-2 text-fg-1 text-[13px] font-medium hover:bg-hover transition-colors disabled:text-fg-4 disabled:cursor-default cursor-pointer"
          >
            {isLoadingMore ? "Loading…" : "Load more"}
          </button>
        </div>
      )}
    </div>
  );
}

function CardRow({ card }: { card: CardSummary }) {
  const meta = [
    capitalizeStr(card.variant),
    card.rarity ? capitalizeStr(card.rarity) : null,
    card.set_name,
  ].filter(Boolean).join(" · ");

  return (
    <Link href={`/registry/cards/${card.card_id}?variant=${card.variant}`} className="no-underline">
      <div className="flex items-center gap-4 px-4 py-[14px] rounded-md border border-border bg-surface hover:bg-[rgba(51,65,85,0.30)] hover:border-border-2 transition-colors cursor-pointer">
        {/* Card thumbnail */}
        <div className="w-12 h-[66px] rounded-md bg-input border border-border shrink-0 overflow-hidden">
          {card.image_small && (
            <img src={card.image_small} alt="" className="w-full h-full object-cover block" />
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0 flex flex-col gap-[3px]">
          <span className="text-[14px] font-semibold text-fg-1 truncate">{card.name}</span>
          <span className="text-[12px] text-fg-3 truncate">{meta}</span>
        </div>

        {/* Price */}
        <span className="font-mono tabular-nums text-[14px] font-medium text-fg-1 shrink-0">
          {card.current_price != null ? formatPrice(card.current_price) : "—"}
        </span>
      </div>
    </Link>
  );
}

function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 px-4 py-[14px] rounded-md border border-border bg-surface">
      <div className="w-12 h-[66px] rounded-md bg-elevated shrink-0 animate-pulse" />
      <div className="flex-1 flex flex-col gap-2">
        <div className="h-3 w-2/5 rounded bg-elevated animate-pulse" />
        <div className="h-2.5 w-3/5 rounded bg-elevated animate-pulse" />
      </div>
      <div className="w-14 h-3 rounded bg-elevated animate-pulse" />
    </div>
  );
}
