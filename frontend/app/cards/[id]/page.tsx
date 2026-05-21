import { getCardPrices, predict } from "@/lib/api";

export default async function CardPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ variant?: string }>;
}) {
  const { id } = await params;
  const { variant: variantParam } = await searchParams;
  const variant = variantParam ?? "normal";

  const [prices, prediction] = await Promise.all([
    getCardPrices({ card_id: id, variant }),
    predict(id, variant),
  ]);

  return <div>{prices.name}</div>;
}
