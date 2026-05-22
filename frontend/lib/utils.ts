import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

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