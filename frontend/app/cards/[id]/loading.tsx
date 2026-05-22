export default function CardLoading() {
  return (
    <div className="flex gap-8 font-[family-name:var(--font-rubik)] animate-pulse">
      <div className="w-[300px] h-[420px] rounded-xl bg-stone-800 shrink-0" />
      <div className="flex flex-col gap-6 pt-2 flex-1">
        <div className="flex flex-col gap-2">
          <div className="h-6 w-64 rounded bg-stone-800" />
          <div className="h-4 w-32 rounded bg-stone-800" />
          <div className="h-4 w-48 rounded bg-stone-800" />
        </div>
        <div className="flex flex-col gap-3">
          <div className="h-3 w-24 rounded bg-stone-800" />
          <div className="h-[300px] w-full rounded-lg bg-stone-800" />
        </div>
      </div>
    </div>
  );
}
