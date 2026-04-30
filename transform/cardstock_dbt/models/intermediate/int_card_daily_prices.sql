with prices as (
    select * from {{ ref('stg_price_history') }}
),

registry as (
    select * from {{ ref('stg_card_registry') }}
)

select
    p.card_id,
    p.price_date,
    p.nm_price,
    r.name,
    r.set_id,
    r.set_name,
    r.set_release_date,
    r.rarity,
    r.variant,
    r.tcgplayer_market_price
from prices p
left join registry r on p.card_id = r.card_id and p.variant = r.variant