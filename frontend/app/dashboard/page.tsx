import KPITile from "@/components/KPITile/KPITile";
import { ApiError, getMarketAggregates, getPredictionMovers, getActualMovers } from "@/lib/api";
import { notFound } from "next/navigation";
import {
  formatRoundedPrice,
  formatPct,
  pctTone,
  formatDate,
  formatPrice,
  capitalizeStr,
  formatLogReturnPct,
  formatNumber,
} from "@/lib/format";
import LeaderboardTable from "./_components/LeaderboardTable";

export default async function DashboardPage() {

  const [aggregates, predictMovers, actualMovers] = await Promise.all([
    getMarketAggregates().catch((e: unknown) => {
      if (e instanceof ApiError && e.status === 404) notFound();
      throw e;
    }),
    getPredictionMovers().catch((e: unknown) => {
      if (e instanceof ApiError && e.status === 404) notFound();
      throw e;
    }),
    getActualMovers().catch((e: unknown) => {
      if (e instanceof ApiError && e.status === 404) notFound();
      throw e;
    }),
  ]);

  const capChange1m = (aggregates.market_cap != null && aggregates.market_cap_1m != null)
    ? (aggregates.market_cap - aggregates.market_cap_1m) / aggregates.market_cap_1m
    : null;
  const capChange3m = (aggregates.market_cap != null && aggregates.market_cap_3m != null)
    ? (aggregates.market_cap - aggregates.market_cap_3m) / aggregates.market_cap_3m
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
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
          <KPITile
            title="Market Cap"
            subtitle={formatRoundedPrice(aggregates.market_cap)}
            context={`as of ${formatDate(aggregates.date)}`}
          />
          <KPITile
            title="1M Market Change"
            subtitle={capChange1m != null ? formatPct(capChange1m) : "-"}
            context={capChange1m != null && aggregates.market_cap_1m ? `from ${formatRoundedPrice(aggregates.market_cap_1m)}` : undefined}
            subtitleTone={pctTone(capChange1m ?? undefined)}
          /> 
          <KPITile
            title="3M Market Change"
            subtitle={capChange3m != null ? formatPct(capChange3m) : "-"}
            context={capChange3m != null && aggregates.market_cap_3m ? `from ${formatRoundedPrice(aggregates.market_cap_3m)}` : undefined}
            subtitleTone={pctTone(capChange3m ?? undefined)}
          /> 
          <KPITile
            title="Forecast Accuracy"
            subtitle={`MAE ${formatPrice(aggregates.mae)}`}
            context={`RMSE ${formatPrice(aggregates.rmse)}`}
          />
          <KPITile
            title="Tracked Cards"
            subtitle={formatNumber(aggregates.total_cards)}
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <LeaderboardTable
            data={predictMovers}
            suffix="pred"
            title="Top 10 Pred. Movers"
            ariaLabel="Top 10 Prediction Movers"
            columns={[
              { header: "Name", render: (c) => capitalizeStr(c.name), href: (c) => `/registry/cards/${c.card_id}?variant=${c.variant}` },
              { header: "Set", render: (c) => `${capitalizeStr(c.set_name)} (${capitalizeStr(c.variant)})` },
              { header: "Rarity", render: (c) => c.rarity ? capitalizeStr(c.rarity) : "—" },
              { header: "Price", render: (c) => formatPrice(c.monthly_price) },
              {
                header: "Pred. Return",
                render: (c) => {
                  const tone = pctTone(c.log_return_3m);
                  const cls = tone === "up" ? "text-bull" : tone === "down" ? "text-bear" : "";
                  return <span className={cls}>{formatLogReturnPct(c.log_return_3m)}</span>
                },
              },
              {
                header: "Pred. Price",
                render: (c) => {
                  const tone = pctTone(c.log_return_3m);
                  const cls = tone === "up" ? "text-bull" : tone === "down" ? "text-bear" : "";
                  return <span className={cls}>{formatPrice(c.pred_3m)}</span>
                },
              },
            ]}
          />
          <LeaderboardTable
            data={actualMovers}
            suffix="actual"
            title="Top 10 Actual Movers"
            ariaLabel="Top 10 Actual Movers"
            columns={[
              { header: "Name", render: (c) => capitalizeStr(c.name), href: (c) => `/registry/cards/${c.card_id}?variant=${c.variant}` },
              { header: "Set", render: (c) => `${capitalizeStr(c.set_name)} (${capitalizeStr(c.variant)})` },
              { header: "Rarity", render: (c) => c.rarity ? capitalizeStr(c.rarity) : "—" },
              { header: "Price 3M Ago", render: (c) => formatPrice(c.monthly_price_3m_ago) },
              {
                header: "Price",
                render: (c) => {
                  const tone = pctTone(c.return_3m);
                  const cls = tone === "up" ? "text-bull" : tone === "down" ? "text-bear" : "";
                  return <span className={cls}>{formatPrice(c.monthly_price)}</span>
                },
              },
              {
                header: "Return",
                render: (c) => {
                  const tone = pctTone(c.return_3m);
                  const cls = tone === "up" ? "text-bull" : tone === "down" ? "text-bear" : "";
                  return <span className={cls}>{formatPct(c.return_3m)}</span>
                },
              },
            ]}
          />
        </div>
      </div>
    </div>
  )
}