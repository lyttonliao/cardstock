with daily as (
    select * from {{ ref('int_card_daily_prices') }}
),

windowed as (
    select
        *,
        avg(monthly_price) over w_3m  as price_ma_3m,
        avg(monthly_price) over w_6m  as price_ma_6m,
        avg(monthly_price) over w_12m as price_ma_12m,
        stddev(monthly_price) over w_3m as price_stddev_3m,
        datediff('day', cast(set_release_date as date), cast(price_date as date)) as days_since_release,
        max(monthly_price) over w_6m as price_6m_high,
        min(monthly_price) over w_6m as price_6m_low,
        (monthly_price - min(monthly_price) over w_6m)
            / nullif(max(monthly_price) over w_6m - min(monthly_price) over w_6m, 0) as stochastic_k_6m,
        (monthly_price - min(monthly_price) over w_3m)
            / nullif(max(monthly_price) over w_3m - min(monthly_price) over w_3m, 0) as stochastic_k_3m,
        monthly_price > avg(monthly_price) over w_3m  as above_ma_3m,
        monthly_price > avg(monthly_price) over w_6m  as above_ma_6m,
        monthly_price > avg(monthly_price) over w_12m as above_ma_12m
    from daily
    window
        w_3m  as (partition by card_id, variant order by price_date::date range between interval '3 months'  preceding and current row),
        w_6m  as (partition by card_id, variant order by price_date::date range between interval '6 months'  preceding and current row),
        w_12m as (partition by card_id, variant order by price_date::date range between interval '12 months' preceding and current row)
),

-- Second CTE needed: build velocity + streak from the computed MA aliases
enriched as (
    select
        *,
        (monthly_price - price_ma_3m)  / nullif(price_ma_3m,  0) as price_change_3m_pct,
        (monthly_price - price_ma_12m) / nullif(price_ma_12m, 0) as price_change_12m_pct,
        ln(monthly_price / nullif(launch_price, 0))               as price_change_since_launch,
        -- Normalised volatility: stddev as a % of price so a $2 swing on a $5 card
        -- isn't invisible compared to a $2 swing on a $500 card
        stddev(monthly_price) over (
            partition by card_id, variant
            order by price_date::date
            range between interval '3 months' preceding and current row
        ) / nullif(monthly_price, 0)                              as price_cv_3m,
        -- How far is the card from its historical peak (running max, no future leakage)?
        -- 1.0 = at all-time high; 0.3 = trading at 30% of ATH
        monthly_price / nullif(price_running_max, 0)              as price_ath_ratio,
        -- How many of the last 12 months has the card been above its 12m moving average?
        -- Sustained uptrend = high value; brief spike = low value
        sum(case when above_ma_12m then 1 else 0 end)
            over (partition by card_id, variant
                  order by price_date::date
                  rows between 11 preceding and current row) as months_above_ma_12m
    from windowed
),

set_releases as (
    select * from {{ ref('int_set_release_features') }}
),

set_index as (
    select * from {{ ref('int_set_price_index') }}
),

google_trends as (
    select * from {{ ref('stg_google_trends') }}
)

select
    e.*,
    case when price_ma_3m > 0 then monthly_price / price_ma_3m end as price_momentum_3m,
    s.days_since_recent_set_release,
    s.hype_weighted_release_90d,
    g.interest_score                                               as pokemon_interest_score,
    extract('month' from e.price_date)                             as month_of_year,
    -- How expensive is this card relative to the average card in its set?
    -- > 1 = chase card; < 1 = below-average card in the set
    monthly_price / nullif(si.set_price_index, 0)                 as price_vs_set_index,
    (
        select p2.monthly_price
        from daily p2
        where p2.card_id = e.card_id and p2.variant = e.variant
            and p2.price_date > e.price_date
            and cast(p2.price_date as date) <= cast(e.price_date as date) + interval '31 days'
        order by p2.price_date desc
        limit 1
    ) as next_1m_price,
    (
        select p2.monthly_price
        from daily p2
        where p2.card_id = e.card_id and p2.variant = e.variant
            and p2.price_date > e.price_date
            and cast(p2.price_date as date) <= cast(e.price_date as date) + interval '92 days'
        order by p2.price_date desc
        limit 1
    ) as next_3m_price,
    (
        select p2.monthly_price
        from daily p2
        where p2.card_id = e.card_id and p2.variant = e.variant
            and p2.price_date > e.price_date
            and cast(p2.price_date as date) <= cast(e.price_date as date) + interval '183 days'
        order by p2.price_date desc
        limit 1
    ) as next_6m_price
from enriched e
left join set_releases s on e.price_date = s.price_date
left join set_index si on e.set_id = si.set_id and e.price_date = si.price_date
left join google_trends g
    on date_trunc('month', e.price_date::date) = date_trunc('month', g.trend_date::date)
