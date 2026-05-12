select
    cast(trend_date as date) as trend_date,
    interest_score
from read_parquet('{{ var("data_dir") }}/trends/google_trends.parquet')
