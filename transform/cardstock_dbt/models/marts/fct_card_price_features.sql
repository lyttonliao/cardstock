with daily as (
    select * from {{ ref('int_card_daily_prices') }}
),

windowed as (
    select
        *,
        avg(nm_price) over w_3m as price_ma_3m,
        avg(nm_price) over w_6m as price_ma_6m,
        avg(nm_price) over w_12m as price_ma_12m,
        stddev(nm_price) over w_3m as price_stddev_3m,
        datediff('day', cast(set_release_date as date), cast(price_date as date)) as days_since_release,
        max(nm_price) over w_6m as price_6m_high,
        min(nm_price) over w_6m as price_6m_low,
        (nm_price - min(nm_price) over w_6m)
            / nullif(max(nm_price) over w_6m - min(nm_price) over w_6m, 0) as stochastic_k_6m,
        (nm_price - min(nm_price) over w_3m)
            / nullif(max(nm_price) over w_3m - min(nm_price) over w_3m, 0) as stochastic_k_3m,
        nm_price > price_ma_3m as above_ma_3m,
        nm_price > price_ma_6m as above_ma_6m
    from daily
    window
        w_3m as (partition by card_id, variant order by price_date::date range between interval '3 months'  preceding and current row),
        w_6m as (partition by card_id, variant order by price_date::date range between interval '6 months'  preceding and current row),
        w_12m as (partition by card_id, variant order by price_date::date range between interval '12 months' preceding and current row)
)

select
    *,
    case when price_ma_3m > 0 then nm_price / price_ma_3m end as price_momentum_3m,
    (
        select p2.nm_price
        from daily p2
        where p2.card_id = p.card_id and p2.variant = p.variant
            and p2.price_date > p.price_date
            and cast(p2.price_date as date) <= cast(p.price_date as date) + interval '31 days'
        order by p2.price_date desc
        limit 1
    ) as next_1m_price,
    (
        select p2.nm_price
        from daily p2
        where p2.card_id = p.card_id and p2.variant = p.variant
            and p2.price_date > p.price_date
            and cast(p2.price_date as date) <= cast(p.price_date as date) + interval '92 days'
        order by p2.price_date desc
        limit 1
    ) as next_3m_price,
    (
        select p2.nm_price
        from daily p2
        where p2.card_id = p.card_id and p2.variant = p.variant
            and p2.price_date > p.price_date
            and cast(p2.price_date as date) <= cast(p.price_date as date) + interval '183 days'
        order by p2.price_date desc
        limit 1
    ) as next_6m_price,
    extract('month' from price_date) as month_of_year
from windowed p
