select
    id as card_id, cast(date as date) as price_date, price as nm_price
from
    read_parquet('{{ var("data_dir") }}/prices/price_history.parquet')