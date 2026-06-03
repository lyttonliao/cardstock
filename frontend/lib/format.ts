export function capitalizeStr(str: string): string {
  return str.split(" ").map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
}

export function formatDate(dateStr: string) {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", { month: "short", year: "numeric", timeZone: "UTC" });
}

export function formatPrice(value: number) {
  return `$${value.toFixed(2)}`;
}

export function formatPct(decimal: number | undefined): string {
  if (decimal == null) return "—";
  const pct = decimal * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
}

export function formatRoundedPrice(value: number) {
  if (value > Math.pow(10, 9)) return `$${Math.ceil(value / Math.pow(10, 6))}M`;
  if (value > Math.pow(10, 6)) return `$${Math.ceil(value / Math.pow(10, 6))}M`;
  if (value > Math.pow(10, 3)) return `$${Math.ceil(value / Math.pow(10, 3))}K`;
  return `$${Math.round(value)}`;
}

export function formatLogReturnPct(logReturn: number | undefined): string {
  if (logReturn == null) return "—";
  const pct = (Math.exp(logReturn) - 1) * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
}

export function pctTone(decimal: number | undefined): "up" | "down" | "neutral" {
  if (decimal == null) return "neutral";
  return decimal >= 0 ? "up" : "down";
}

export function boolTone(val: boolean | undefined): "up" | "down" | "neutral" {
  if (val == null) return "neutral";
  return val ? "up" : "down";
}

export function fmt(val: number | null | undefined, fn: (n: number) => string): string {
  return val != null ? fn(val) : "—";
}

export function formatNumber(n: number | null | undefined): string {
  if (n == null) return "-";
  return new Intl.NumberFormat("en-US").format(n);
}
