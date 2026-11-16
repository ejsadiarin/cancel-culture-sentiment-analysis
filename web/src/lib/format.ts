export const WINDOW_ORDER = ["pre", "cancel", "post"] as const;

export const WINDOW_LABEL = {
  pre: "Before",
  cancel: "Apology",
  post: "After",
} as const;

export const WINDOW_LONG = {
  pre: "Before the apology",
  cancel: "The apology video",
  post: "After the apology",
} as const;

export const SENTIMENT_LABEL = {
  POSITIVE: "Positive",
  NEGATIVE: "Negative",
  NEUTRAL: "Neutral",
} as const;

export function fmtInt(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

export function fmtCompact(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}m`;
  if (value >= 10_000) return `${(value / 1_000).toFixed(1)}k`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}k`;
  return fmtInt(value);
}

export function fmtDecimal(value: number, digits = 3): string {
  return value.toFixed(digits);
}

export function fmtPct(value: number, digits = 1): string {
  return `${value.toFixed(digits)}%`;
}

export function fmtSignedPct(value: number, digits = 1): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

export function fmtP(value: number): string {
  if (value < 0.001) return "< 0.001";
  return value.toFixed(3);
}

export function fmtR(value: number): string {
  return `${value > 0 ? "+" : "−"}${Math.abs(value).toFixed(3)}`;
}

export function fmtDensity(value: number): string {
  return `${(value * 10_000).toFixed(2)}`;
}

export function fmtMetric(value: number, key: string): string {
  if (key === "density") return (value * 10_000).toFixed(2);
  if (key === "modularity") return value.toFixed(2);
  if (key === "cascade_depth") return value.toFixed(0);
  if (key === "in_degree_mean") return value.toFixed(2);
  if (key === "degree_gini") return value.toFixed(2);
  if (key === "degree_variance") return value.toFixed(1);
  if (key === "hub_dominance") return value.toFixed(0);
  if (Math.abs(value) >= 1_000) return fmtCompact(value);
  return value.toFixed(2);
}

export function fmtDate(iso: string): string {
  const date = new Date(`${iso}T12:00:00`);
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

export function fmtDateShort(iso: string): string {
  const date = new Date(`${iso}T12:00:00`);
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
  }).format(date);
}

export function slotLabel(slot: string): string {
  if (slot === "cancel-1") return "Apology";
  const [window, number] = slot.split("-");
  return `${WINDOW_LABEL[window as keyof typeof WINDOW_LABEL]} ${number}`;
}

export function slotShort(slot: string): string {
  if (slot === "cancel-1") return "AP";
  const [window, number] = slot.split("-");
  return `${window === "pre" ? "P" : "A"}${number}`;
}

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function linearScale(
  value: number,
  domainMin: number,
  domainMax: number,
  rangeMin: number,
  rangeMax: number,
): number {
  if (domainMax === domainMin) return (rangeMin + rangeMax) / 2;
  const t = (value - domainMin) / (domainMax - domainMin);
  return rangeMin + t * (rangeMax - rangeMin);
}

export function niceTicks(min: number, max: number, count = 5): number[] {
  if (max === min) return [min];
  const span = max - min;
  const rawStep = span / (count - 1);
  const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
  const residual = rawStep / magnitude;
  const step =
    residual >= 7.5 ? 10 * magnitude : residual >= 3.5 ? 5 * magnitude : residual >= 1.5 ? 2 * magnitude : magnitude;
  const start = Math.ceil(min / step) * step;
  const ticks: number[] = [];
  for (let value = start; value <= max + step * 0.01; value += step) {
    ticks.push(Number(value.toFixed(10)));
  }
  return ticks;
}

export function smoothPath(points: Array<{ x: number; y: number }>): string {
  if (points.length < 2) return "";
  let d = `M ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)}`;
  for (let i = 0; i < points.length - 1; i += 1) {
    const p0 = points[i - 1] ?? points[i];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[i + 2] ?? p2;
    const tension = 0.18;
    const c1x = p1.x + (p2.x - p0.x) * tension;
    const c1y = p1.y + (p2.y - p0.y) * tension;
    const c2x = p2.x - (p3.x - p1.x) * tension;
    const c2y = p2.y - (p3.y - p1.y) * tension;
    d += ` C ${c1x.toFixed(2)} ${c1y.toFixed(2)}, ${c2x.toFixed(2)} ${c2y.toFixed(2)}, ${p2.x.toFixed(2)} ${p2.y.toFixed(2)}`;
  }
  return d;
}

export function useReducedMotion(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
