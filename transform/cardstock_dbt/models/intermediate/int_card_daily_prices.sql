with pc_prices as (
    -- PriceCharting historical monthly snapshots (bootstrap only — no longer updated)
    select * from {{ ref('stg_price_history') }}
),

registry as (
    select * from {{ ref('stg_card_registry') }}
),

-- Aggregate TCGPlayer daily prices to monthly averages.
-- Used both to fill in months with no PriceCharting snapshot (daily_fill below)
-- and to compute intra-month stats on rows that do have a PriceCharting anchor.
daily_prices_monthly as (
    select
        card_id,
        variant,
        date_trunc('month', price_date)::date                                as price_month,
        avg(tcgplayer_market_price)                                          as daily_price,
        stddev(tcgplayer_market_price)                                       as daily_price_stddev,
        max(tcgplayer_market_price)                                          as daily_price_high,
        min(tcgplayer_market_price)                                          as daily_price_low,
        (max(tcgplayer_market_price) - min(tcgplayer_market_price))
            / nullif(avg(tcgplayer_market_price), 0)                         as daily_range_pct,
        -- First and last daily price in the month — used to compute intramonth return in the mart
        arg_min(tcgplayer_market_price, price_date)                          as daily_price_month_open,
        arg_max(tcgplayer_market_price, price_date)                          as daily_price_month_close,
        -- How many distinct days of TCGPlayer data exist this month.
        -- 0 (NULL after join) = eBay/vintage card with no TCGPlayer activity;
        -- the model uses this to down-weight daily features for illiquid cards.
        count(distinct price_date)                                           as daily_day_count
    from {{ ref('stg_daily_price_history') }}
    group by 1, 2, 3
),

-- Synthetic monthly rows: one per (card, variant, month) where daily prices exist
-- but no PriceCharting snapshot was ever scraped for that month.
-- This lets the fact table grow automatically as daily prices accumulate,
-- without needing to run the PriceCharting scraper again.
daily_fill as (
    select
        dm.card_id,
        dm.variant,
        dm.price_month    as price_date,
        dm.daily_price    as nm_price   -- monthly_price = daily avg for these rows
    from daily_prices_monthly dm
    where not exists (
        select 1
        from pc_prices pc
        where pc.card_id = dm.card_id
          and pc.variant  = dm.variant
          and date_trunc('month', pc.price_date)::date = dm.price_month
    )
),

-- Combined price anchor: historical PriceCharting + daily-derived new months
prices as (
    select card_id, variant, price_date, nm_price from pc_prices
    union all
    select card_id, variant, price_date, nm_price from daily_fill
)

select
    p.card_id,
    p.price_date,
    p.nm_price as monthly_price,
    r.name,
    r.set_id,
    r.set_name,
    r.set_release_date,
    r.rarity,
    r.variant,
    r.is_specialty_set,
    r.packs_per_specific_card,
    r.pokedex_number,
    d.daily_price,
    d.daily_price_stddev,
    d.daily_price_high,
    d.daily_price_low,
    d.daily_range_pct,
    d.daily_price_month_open,
    d.daily_price_month_close,
    d.daily_day_count,
    first_value(p.nm_price) over (
        partition by p.card_id, p.variant
        order by p.price_date
    ) as launch_price,
    max(p.nm_price) over (
        partition by p.card_id, p.variant
        order by p.price_date
        rows between unbounded preceding and current row
    ) as price_running_max
from prices p
left join registry r on p.card_id = r.card_id and p.variant = r.variant
left join daily_prices_monthly d
    on p.card_id = d.card_id
    and p.variant = d.variant
    and date_trunc('month', p.price_date)::date = d.price_month
