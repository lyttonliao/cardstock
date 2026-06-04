"use client";

export default function GlobalError() {
  return (
    <div className="flex flex-col gap-2 py-16 items-center text-center">
      <p className="text-sm font-medium text-fg-2">Something went wrong</p>
      <p className="text-xs text-fg-4">An unexpected error occurred. Please try again later.</p>
    </div>
  );
}
