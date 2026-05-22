import { getCardPrices, predict } from "@/lib/api";
import { capitalizeStr, formatDate, formatPrice } from "@/lib/utils";
import PriceChart from "@/components/PriceChart/PriceChart";

function formatPct(decimal: number | undefined): string {
  if (decimal == null) return "—";
  const pct = decimal * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
}

function formatLogReturnPct(logReturn: number | undefined): string {
  if (logReturn == null) return "—";
  const pct = (Math.exp(logReturn) - 1) * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
}

function pctColor(decimal: number | undefined): string {
  if (decimal == null) return "text-white";
  return decimal >= 0 ? "text-emerald-400" : "text-red-400";
}

function boolColor(val: boolean | undefined): string {
  if (val == null) return "text-white";
  return val ? "text-emerald-400" : "text-red-400";
}

function fmt(val: number | null | undefined, fn: (n: number) => string): string {
  return val != null ? fn(val) : "—";
}

function SectionHeader({ title }: { title: string }) {
  return (
    <div className="flex items-center gap-4 mb-5">
      <p className="text-xs text-stone-500 uppercase tracking-widest whitespace-nowrap">{title}</p>
      <div className="h-px bg-stone-800 flex-1" />
    </div>
  );
}

function Stat({ label, value, valueClass = "text-white" }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="flex flex-col gap-1">
      <p className="text-xs text-stone-500">{label}</p>
      <p className={`text-base font-medium ${valueClass}`}>{value}</p>
    </div>
  );
}

export default async function CardPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ variant?: string }>;
}) {
  const { id } = await params;
  const { variant: variantParam } = await searchParams;
  const variant = variantParam ?? "normal";

  const [prices, prediction] = await Promise.all([
    getCardPrices({ card_id: id, variant }),
    predict(id, variant),
  ]);

  const lastMonthlyPrice = prices.prices.findLast((p) => p.monthly_price !== null) ?? null;
  const { moving_averages, momentum, volatility, trend, market_context, forecast } = prediction;
  const predPrices = prediction.prices;

  return (
    <div className="font-[family-name:var(--font-rubik)]">
      {/* Card header */}
      <div className="flex gap-8 mb-12">
        <img
          src={prices.image_large}
          className="w-[300px] rounded-xl shadow-2xl shadow-black/60 self-start"
        />
        <div className="flex flex-col gap-6 pt-2 flex-1">
          <div>
            <h1 className="text-xl font-bold text-white break-words">
              {`${prices.name} - ${prices.set_name}`}
            </h1>
            <div className="flex gap-2 mt-1 items-center">
              <span className="text-sm text-stone-400">{capitalizeStr(prices.variant)}</span>
              {prices.rarity && (
                <>
                  <span className="text-stone-400">•</span>
                  <span className="text-sm text-stone-400">{capitalizeStr(prices.rarity)}</span>
                </>
              )}
            </div>
            {lastMonthlyPrice && (
              <p className="text-stone-400 text-sm mt-1">
                Market Price as of {formatDate(lastMonthlyPrice.price_date)}: {formatPrice(lastMonthlyPrice.monthly_price!)}
              </p>
            )}
          </div>
          <div>
            <p className="text-xs text-stone-500 uppercase tracking-widest mb-3">Price History</p>
            <PriceChart prices={prices.prices} />
          </div>
        </div>
      </div>

      {/* Forecast — most prominent */}
      <div className="mb-12">
        <SectionHeader title="Forecast" />
        <div className="flex gap-12">
          <Stat label="Predicted 3M Price" value={formatPrice(forecast.predicted_3m_price)} />
          <Stat
            label="Expected 3M Return"
            value={formatLogReturnPct(forecast.log_return_3m)}
            valueClass={pctColor(forecast.log_return_3m)}
          />
          {forecast.actual_next_1m_price != null && (
            <Stat label="Actual 1M Price" value={formatPrice(forecast.actual_next_1m_price)} />
          )}
          {forecast.actual_next_3m_price != null && (
            <Stat label="Actual 3M Price" value={formatPrice(forecast.actual_next_3m_price)} />
          )}
          {forecast.actual_next_6m_price != null && (
            <Stat label="Actual 6M Price" value={formatPrice(forecast.actual_next_6m_price)} />
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8">
        {/* Prices */}
        <div className="mb-6">
          <SectionHeader title="Prices" />
          <div className="flex gap-12">
            <Stat label="Monthly" value={fmt(predPrices.monthly_price, formatPrice)} />
            <Stat label="Daily" value={fmt(predPrices.daily_price, formatPrice)} />
            <Stat label="Launch" value={fmt(predPrices.launch_price, formatPrice)} />
            <Stat label="All-Time High" value={fmt(predPrices.all_time_high, formatPrice)} />
          </div>
        </div>

        {/* Moving Averages */}
        <div className="mb-6">
          <SectionHeader title="Moving Averages" />
          <div className="flex gap-12">
            <Stat label="3M Avg" value={fmt(moving_averages.ma_3m, formatPrice)} />
            <Stat label="6M Avg" value={fmt(moving_averages.ma_6m, formatPrice)} />
            <Stat label="12M Avg" value={fmt(moving_averages.ma_12m, formatPrice)} />
          </div>
        </div>

        {/* Momentum */}
        <div className="mb-6">
          <SectionHeader title="Momentum" />
          <div className="flex gap-12">
            <Stat
              label="Price / 3M MA"
              value={momentum.price_momentum_3m != null ? `${momentum.price_momentum_3m.toFixed(2)}x` : "—"}
            />
            <Stat label="vs. 3M MA" value={formatPct(momentum.price_change_3m_pct)} valueClass={pctColor(momentum.price_change_3m_pct)} />
            <Stat label="vs. 12M MA" value={formatPct(momentum.price_change_12m_pct)} valueClass={pctColor(momentum.price_change_12m_pct)} />
            <Stat label="Since Launch" value={formatLogReturnPct(momentum.price_change_since_launch)} valueClass={pctColor(momentum.price_change_since_launch)} />
          </div>
        </div>

        {/* Volatility */}
        <div className="mb-6">
          <SectionHeader title="Volatility" />
          <div className="flex gap-12">
            <Stat label="3M Std Dev" value={fmt(volatility.stddev_3m, formatPrice)} />
            <Stat label="3M Coeff. of Variation" value={formatPct(volatility.cv_3m)} />
            <Stat label="6M High" value={fmt(volatility.price_6m_high, formatPrice)} />
            <Stat label="6M Low" value={fmt(volatility.price_6m_low, formatPrice)} />
            <Stat label="Stochastic K (6M)" value={formatPct(volatility.stochastic_k_6m)} />
            <Stat label="Stochastic K (3M)" value={formatPct(volatility.stochastic_k_3m)} />
          </div>
        </div>

        {/* Trend */}
        <div className="mb-6">
          <SectionHeader title="Trend" />
          <div className="flex gap-12">
            <Stat
              label="Above 3M MA"
              value={trend.above_ma_3m != null ? (trend.above_ma_3m ? "Yes" : "No") : "—"}
              valueClass={boolColor(trend.above_ma_3m)}
            />
            <Stat
              label="Above 6M MA"
              value={trend.above_ma_6m != null ? (trend.above_ma_6m ? "Yes" : "No") : "—"}
              valueClass={boolColor(trend.above_ma_6m)}
            />
            <Stat
              label="Above 12M MA"
              value={trend.above_ma_12m != null ? (trend.above_ma_12m ? "Yes" : "No") : "—"}
              valueClass={boolColor(trend.above_ma_12m)}
            />
            <Stat
              label="Months Above 12M MA"
              value={trend.months_above_ma_12m != null ? `${trend.months_above_ma_12m} / 12` : "—"}
            />
            <Stat label="% of ATH" value={formatPct(trend.price_ath_ratio)} />
            <Stat
              label="vs. Set Index"
              value={trend.price_vs_set_index != null ? `${trend.price_vs_set_index.toFixed(2)}x` : "—"}
            />
          </div>
        </div>

        {/* Market Context */}
        <div className="mb-6">
          <SectionHeader title="Market Context" />
          <div className="flex gap-12">
            <Stat
              label="Interest Score"
              value={market_context.pokemon_interest_score != null ? market_context.pokemon_interest_score.toFixed(1) : "—"}
            />
            <Stat
              label="Days Since Set Release"
              value={market_context.days_since_release != null ? `${market_context.days_since_release}d` : "—"}
            />
            <Stat
              label="Recent Set Release"
              value={market_context.days_since_recent_set_release != null ? `${market_context.days_since_recent_set_release}d ago` : "—"}
            />
            <Stat
              label="Hype Score (90d)"
              value={market_context.hype_weighted_release_90d != null ? market_context.hype_weighted_release_90d.toFixed(2) : "—"}
            />
            <Stat
              label="Specialty Set"
              value={market_context.is_specialty_set ? "Yes" : "No"}
            />
            <Stat
              label="Packs / Card"
              value={market_context.packs_per_specific_card != null ? market_context.packs_per_specific_card.toFixed(1) : "—"}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
