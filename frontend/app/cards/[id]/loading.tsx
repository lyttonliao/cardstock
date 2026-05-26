export default function CardLoading() {
  return (
    <div className="flex gap-8 font-display animate-pulse">
      <div className="w-[300px] h-[420px] rounded-[20px] bg-elevated shrink-0" />
      <div className="flex flex-col gap-6 pt-2 flex-1">
        <div className="flex flex-col gap-2">
          <div className="h-6 w-64 rounded bg-elevated" />
          <div className="h-4 w-32 rounded bg-elevated" />
          <div className="h-4 w-48 rounded bg-elevated" />
        </div>
        <div className="flex flex-col gap-3">
          <div className="h-3 w-24 rounded bg-elevated" />
          <div className="h-[300px] w-full rounded-lg bg-elevated" />
        </div>
      </div>
    </div>
  );
}
