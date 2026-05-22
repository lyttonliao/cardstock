export interface CardSummary {
  card_id: string,
  name: string,
  rarity: string | null,
  set_id: string,
  set_name: string,
  variant: string,
  set_release_date: string | null,
  image_small: string,
  current_price: number | null,
}

export interface CardListResponse {
  total: number,
  page: number,
  page_size: number,
  items: CardSummary[],
}

export interface CardSearchParams {
  name?: string,
  set_id?: string,
  rarity?: string,
  variant?: string,
  page?: number,
  page_size?: number,
}

export interface PricePoint {
  price_date: string,
  monthly_price: number | null,
  daily_price: number | null,
}

export interface PriceHistoryResponse {
  card_id: string,
  name: string,
  variant: string,
  rarity: string | null,
  set_id: string,
  set_name: string,
  image_small: string,
  image_large: string,
  prices: PricePoint[],
}

interface PriceMetrics {
  monthly_price: number | null,
  daily_price: number | null,
  launch_price: number | null,
  all_time_high: number | null,
}

interface MovingAverages {
  ma_3m?: number,
  ma_6m?: number,
  ma_12m?: number,
}

interface Momentum {
  price_momentum_3m?: number,
  price_change_3m_pct?: number,
  price_change_12m_pct?: number,
  price_change_since_launch?: number,
}

interface Volatility {
  stddev_3m?: number,
  cv_3m?: number,
  price_6m_high?: number,
  price_6m_low?: number,
  stochastic_k_6m?: number,
  stochastic_k_3m?: number,
}

interface TrendRegime {
  above_ma_3m?: boolean,
  above_ma_6m?: boolean,
  above_ma_12m?: boolean,
  months_above_ma_12m?: number,
  price_ath_ratio?: number,
  price_vs_set_index?: number,
}

interface MarketContext {
  pokemon_interest_score?: number,
  days_since_recent_set_release?: number,
  hype_weighted_release_90d?: number,
  days_since_release?: number,
  is_specialty_set: boolean,
  packs_per_specific_card?: number,
}

interface Forecast {
  predicted_3m_price: number,
  log_return_3m: number,
  actual_next_1m_price?: number,
  actual_next_3m_price?: number,
  actual_next_6m_price?: number,
}

export interface PredictResponse {
  card_id: string,
  name: string,
  variant: string,
  rarity: string | null,
  set_id: string,
  set_name: string,
  price_date: string,
  prices: PriceMetrics,
  moving_averages: MovingAverages,
  momentum: Momentum,
  volatility: Volatility,
  trend: TrendRegime,
  market_context: MarketContext,
  forecast: Forecast,
}

interface ModelMetrics {
  mae_dollars: number,
  rmse_dollars: number,
  evaluation_set: string,
}

export interface ModelInfoResponse {
  model_version: string,
  model_type: string,
  objective: string,
  target: string,
  n_estimators: number,
  learning_rate: number,
  max_depth: number,
  n_features: number,
  features: string[],
  train_cutoff: string,
  metrics: ModelMetrics
}

export interface CardPricesSearchParams {
  card_id: string,
  variant: string,
  from_date?: string,
  to_date?: string,
}