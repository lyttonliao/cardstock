"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { PricePoint } from "@/types/api";
import { formatDate, formatPrice } from "@/lib/utils";


export default function PriceChart({ prices }: { prices: PricePoint[] }) {
  const data = prices
    .filter((p): p is PricePoint & { monthly_price: number } => p.monthly_price !== null)
    .map((p) => ({
      date: formatDate(p.price_date),
      price: p.monthly_price,
    }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#292524" />
        <XAxis
          dataKey="date"
          tick={{ fill: "#78716c", fontSize: 12 }}
          tickLine={true}
          axisLine={true}
          interval="preserveStartEnd"
        />
        <YAxis
          tickFormatter={formatPrice}
          tick={{ fill: "#78716c", fontSize: 12 }}
          tickLine={true}
          axisLine={true}
          width={60}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1c1917",
            border: "1px solid #292524",
            borderRadius: "8px",
            color: "#fff",
          }}
          formatter={(value) => [formatPrice(value as number), "Price"]}
          labelStyle={{ color: "#a8a29e" }}
        />
        <Line
          type="monotone"
          dataKey="price"
          stroke="#f97316"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: "#f97316" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
