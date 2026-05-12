-- For each monthly price snapshot date, compute:
--   days_since_recent_set_release : days since the most recent set dropped
--   hype_weighted_release_90d     : sum of avg card launch prices for sets released
--                                   in the trailing 90 days
--
-- set_hype_score = avg card price at first capture after release
--
-- The overall market temperature (Google Trends) is captured separately
-- as pokemon_interest_score in fct_card_price_features.

with price_dates as (
    select distinct price_date
    from {{ ref('stg_price_history') }}
),

-- For each card, take the very first price snapshot on or after the set's release date.
-- Recent sets → launch price. Legacy sets (pre-Dec 2020) → earliest available data.
card_at_release as (
    select
        r.set_id,
        r.set_release_date,
        p.nm_price
    from {{ ref('stg_card_registry') }} r
    join {{ ref('stg_price_history') }} p
        on r.card_id = p.card_id and r.variant = p.variant
    where
        r.set_release_date is not null
        and p.price_date >= r.set_release_date
    qualify row_number() over (
        partition by r.card_id, r.variant
        order by p.price_date
    ) = 1
),

-- Average card price at launch per set — pure set quality signal.
-- Market temperature is kept separate (pokemon_interest_score in the mart).
set_hype_scores as (
    select
        set_id,
        set_release_date,
        avg(nm_price) as set_hype_score
    from card_at_release
    group by set_id, set_release_date
),

-- Cross join: for each price_date, all sets already released by that date
crossed as (
    select
        p.price_date,
        h.set_release_date                                     as release_date,
        h.set_hype_score,
        datediff('day', h.set_release_date, p.price_date)     as days_since_release
    from price_dates p
    cross join set_hype_scores h
    where h.set_release_date <= p.price_date
)

select
    price_date,
    min(days_since_release)                                                           as days_since_recent_set_release,
    coalesce(sum(set_hype_score) filter (where days_since_release <= 90), 0)          as hype_weighted_release_90d
from crossed
group by price_date
