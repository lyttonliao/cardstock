-- For each (set_id, price_date), the average NM price across all tracked cards in the set.
-- Used to compute price_vs_set_index in the mart: a ratio > 1 means the card is more
-- expensive than a typical card in its set (chase card); < 1 means below average (bulk rare).

select
    set_id,
    price_date,
    avg(monthly_price) as set_price_index
from {{ ref('int_card_daily_prices') }}
where set_id is not null
group by set_id, price_date
