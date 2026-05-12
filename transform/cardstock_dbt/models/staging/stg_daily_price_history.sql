select
    id as card_id,
    cast(date as date) as price_date,
    market_price as tcgplayer_market_price,
    variant
from read_parquet('{{ var("data_dir") }}/prices/daily_price_history.parquet')