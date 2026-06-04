"use client";

export default function CardError() {
  return (
    <div className="flex flex-col gap-2 py-16 items-center text-center">
      <p className="text-sm font-medium text-fg-2">Unable to load card</p>
      <p className="text-xs text-fg-4">This card could not be fetched. The data service may be temporarily unavailable.</p>
    </div>
  );
}
