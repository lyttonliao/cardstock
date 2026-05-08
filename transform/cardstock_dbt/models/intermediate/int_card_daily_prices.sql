with prices as (
    select * from {{ ref('stg_price_history') }}
),

registry as (
    select * from {{ ref('stg_card_registry') }}
),

daily_prices as (
    select * from {{ ref('stg_daily_price_history') }}
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
    d.tcgplayer_market_price as daily_price
from prices p
left join registry r on p.card_id = r.card_id and p.variant = r.variant
left join daily_prices d on p.card_id = d.card_id