import {
  CardSearchParams,
  CardListResponse,
  PriceHistoryResponse,
  CardPricesSearchParams,
  PredictResponse,
  ModelInfoResponse
} from "../types/api"

const BASE = process.env.NEXT_PUBLIC_API_URL

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  const data = await res.json();
  if (!res.ok) {
    console.error("API error", res.status, JSON.stringify(data));
    throw new Error(`API error ${res.status}`);
  }
  console.log("API response", JSON.stringify(data).slice(0, 500));
  return data;
}

export function getCards(params: CardSearchParams): Promise<CardListResponse> {
  const query = new URLSearchParams();

  if (params.name) query.set("name", params.name);
  if (params.variant) query.set("variant", params.variant);
  if (params.rarity) query.set("rarity", params.rarity);
  if (params.set_id) query.set("set_id", params.set_id);
  if (params.page != null) query.set("page", String(params.page));
  if (params.page_size != null) query.set("page_size", String(params.page_size));

  return apiFetch<CardListResponse>(`/cards?${query}`);
}

export function getCardPrices(params: CardPricesSearchParams): Promise<PriceHistoryResponse> {
  const query = new URLSearchParams();

  if (params.from_date) query.set("from_date", params.from_date);
  if (params.to_date) query.set("to_date", params.to_date);
  query.set("variant", params.variant);

  return apiFetch<PriceHistoryResponse>(`/cards/${params.card_id}/prices?${query}`);
}

export function predict(cardId: string, variant: string): Promise<PredictResponse> {
  return apiFetch<PredictResponse>('/predict', {
    method: "POST",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ card_id: cardId, variant }),
  })
}

export function getModelInfo(): Promise<ModelInfoResponse> {
  return apiFetch<ModelInfoResponse>('/model/info');
}