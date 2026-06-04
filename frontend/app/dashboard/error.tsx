"use client";

export default function DashboardError() {
  return (
    <div className="flex flex-col gap-2 py-16 items-center text-center">
      <p className="text-sm font-medium text-fg-2">Unable to load dashboard</p>
      <p className="text-xs text-fg-4">The market data service is temporarily unavailable. Try again later.</p>
    </div>
  );
}
