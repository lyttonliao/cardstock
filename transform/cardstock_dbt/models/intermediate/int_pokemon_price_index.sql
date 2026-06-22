-- Cross-card features grouped by Pokémon species (pokedex_number).
-- For each (pokedex_number, price_date) combination, aggregates price levels
-- and 3-month momentum across all tracked cards of that species.
--
-- Captures the "halo effect": if a flagship Charizard card spikes, do secondary
-- Charizard cards move in parallel? pokemon_avg_price_change_3m answers this directly.
--
-- Cards without a pokedex_number (Trainer cards, Energy cards, some older sets)
-- are excluded from aggregation; those rows get NULL pokemon_* features in the mart.

with cards as (
    select * from {{ ref('int_card_daily_prices') }}
),

registry as (
    select distinct card_id, variant, pokedex_number
    from {{ ref('stg_card_registry') }}
    where pokedex_number is not null
),

-- Compute per-card 3-month price change before aggregating across species.
-- lag(3) at monthly granularity = 3 months ago.
card_changes as (
    select
        c.card_id,
        c.variant,
        c.price_date,
        c.monthly_price,
        r.pokedex_number,
        lag(c.monthly_price, 3) over (
            partition by c.card_id, c.variant order by c.price_date
        ) as price_3m_ago
    from cards c
    inner join registry r on c.card_id = r.card_id and c.variant = r.variant
)

select
    pokedex_number,
    price_date,
    count(*)                                                            as pokemon_num_cards,
    avg(monthly_price)                                                  as pokemon_avg_price,
    max(monthly_price)                                                  as pokemon_max_price,
    -- Average 3m price change across all cards of this species.
    -- Positive = whole species trending up; negative = sector-wide decline.
    avg(
        (monthly_price - price_3m_ago) / nullif(price_3m_ago, 0)
    )                                                                   as pokemon_avg_price_change_3m
from card_changes
group by pokedex_number, price_date
