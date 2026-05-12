select
    id as card_id,
    name,
    number,
    rarity,
    set_id,
    set_name,
    cast(replace(set_release_date, '/', '-') as date) as set_release_date,
    variant,
    image_small,
    image_large,
    tcgplayer_url,
    tcgplayer_market_price,
    is_specialty_set,
    packs_per_specific_card
from 
    read_parquet('{{ var("data_dir") }}/registry/card_registry.parquet')