export default function DashboardLoading() {
  return (
    <div className="flex flex-col gap-8 animate-pulse">
      <div>
        <div className="flex items-center gap-3 mb-5">
          <h2 className="text-[15px] font-display text-fg-2 font-semibold uppercase tracking-wide shrink-0">
            Market KPI
          </h2>
          <div className="h-px flex-1 bg-border" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <div className="h-[130px] w-[300px] bg-elevated rounded-xl border border-border"></div>
          <div className="h-[130px] w-[300px] bg-elevated rounded-xl border border-border"></div>
          <div className="h-[130px] w-[300px] bg-elevated rounded-xl border border-border"></div>
          <div className="h-[130px] w-[300px] bg-elevated rounded-xl border border-border"></div>
        </div>
      </div>
      <div>
        <div className="flex items-center gap-3 mb-5">
          <h2 className="text-[15px] font-display text-fg-2 font-semibold uppercase tracking-wide shrink-0">
            Leaderboard
          </h2>
          <div className="h-px flex-1 bg-border" />
        </div>
        <div className="flex flex-col md:flex-row gap-8">
          <div className="h-[600px] w-1/2 bg-elevated" />
          <div className="h-[600px] w-1/2 bg-elevated" />
        </div>
      </div>
    </div>
  )
}