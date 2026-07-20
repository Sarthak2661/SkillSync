export function integer(value: number | null | undefined): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value ?? 0);
}

export function currency(value: number | null | undefined): string {
  if (!value) return "Not available";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function percent(value: number | null | undefined): string {
  return `${Math.round((value ?? 0) * 100)}%`;
}

export function dateTime(value: string | number | null | undefined): string {
  if (!value) return "Not recorded";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

export function labelClass(value: string): string {
  const normalized = value.toLowerCase();
  if (normalized.includes("high") || normalized === "pass" || normalized.includes("verified")) return "badge success";
  if (normalized.includes("warning") || normalized.includes("watch") || normalized.includes("broad")) return "badge warning";
  if (normalized.includes("fail") || normalized.includes("low")) return "badge danger";
  return "badge neutral";
}
