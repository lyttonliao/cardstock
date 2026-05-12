with prices as (
    select * from {{ ref('stg_price_history') }}
),

registry as (
    select * from {{ ref('stg_card_registry') }}
),

-- Aggregate TCGPlayer daily prices to monthly averages so they can join
-- with the monthly PriceCharting snapshots (which fall on the 1st of each month)
daily_prices_monthly as (
    select
        card_id,
        variant,
        date_trunc('month', price_date) as price_month,
        avg(tcgplayer_market_price) as daily_price
    from {{ ref('stg_daily_price_history') }}
    group by 1, 2, 3
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
    d.daily_price,
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
    and date_trunc('month', p.price_date) = d.price_month