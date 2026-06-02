import KPITile from "@/components/KPITile/KPITile";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ApiError, getMarketAggregates } from "@/lib/api";
import { notFound } from "next/navigation";
import {
  formatRoundedPrice,
  formatPct,
  pctTone,
  formatDate,
  formatPrice,
} from "@/lib/format";

export default async function DashboardPage() {

  const data = await getMarketAggregates().catch((e: unknown) => {
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  });

  const capChange1m = (data.market_cap != null && data.market_cap_1m != null)
    ? (data.market_cap - data.market_cap_1m) / data.market_cap_1m
    : null;
  const capChange3m = (data.market_cap != null && data.market_cap_3m != null)
    ? (data.market_cap - data.market_cap_3m) / data.market_cap_3m
    : null;

  return (
    <div className="space-y-8">
      {/* KPI Tiles */}
      <div>
        <div className="flex items-center gap-3 mb-5">
          <h2 className="text-[15px] text-fg-2 font-display font-semibold shrink-0 uppercase tracking-wide">
            Market KPI
          </h2>
          <div className="h-px flex-1 bg-border"/>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <KPITile
            title="Market Cap"
            subtitle={formatRoundedPrice(data.market_cap)}
            context={`as of ${formatDate(data.date)}`}
          />
          <KPITile
            title="1M Market Change"
            subtitle={capChange1m != null ? formatPct(capChange1m) : "-"}
            context={capChange1m != null && data.market_cap_1m ? `from ${formatRoundedPrice(data.market_cap_1m)}` : undefined}
            subtitleTone={pctTone(capChange1m ?? undefined)}
          /> 
          <KPITile
            title="3M Market Change"
            subtitle={capChange3m != null ? formatPct(capChange3m) : "-"}
            context={capChange3m != null && data.market_cap_3m ? `from ${formatRoundedPrice(data.market_cap_3m)}` : undefined}
            subtitleTone={pctTone(capChange3m ?? undefined)}
          /> 
          <KPITile
            title="Forecast Accuracy"
            subtitle={`MSE ${formatPrice(data.mae)}`}
            context={`RMSE ${formatPrice(data.rmse)}`}
          />
        </div>
      </div>

      {/* Leaderboards */}
      <div>
        <div className="flex items-center gap-3 mb-5">
          <h2 className="text-[15px] text-fg-2 font-display font-semibold shrink-0 uppercase tracking-wide">
            Leaderboard
          </h2>
          <div className="h-px flex-1 bg-border" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2">
          
        </div>
      </div>
      
    </div>
  )
}