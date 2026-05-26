import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/types";

export const RISK_META: Record<RiskLevel, { label: string; short: string; className: string; dot: string }> = {
  low: {
    label: "Bajo",
    short: "BAJO",
    className: "border-emerald-200 bg-emerald-50 text-emerald-800",
    dot: "bg-emerald-500",
  },
  moderate: {
    label: "Moderado",
    short: "MODERADO",
    className: "border-amber-200 bg-amber-50 text-amber-800",
    dot: "bg-amber-500",
  },
  high: {
    label: "Alto",
    short: "ALTO",
    className: "border-red-200 bg-red-50 text-red-800",
    dot: "bg-red-500",
  },
  critical: {
    label: "Crítico",
    short: "CRÍTICO",
    className: "border-rose-300 bg-rose-100 text-rose-900",
    dot: "bg-rose-600",
  },
};

export function RiskBadge({ level, compact = false }: { level: RiskLevel; compact?: boolean }) {
  const meta = RISK_META[level];
  return (
    <span
      className={cn(
        "inline-flex h-8 items-center gap-2 rounded-md border px-2.5 text-xs font-semibold",
        meta.className,
      )}
    >
      <span className={cn("h-2 w-2 rounded-full", meta.dot)} />
      {compact ? meta.short : meta.label}
    </span>
  );
}

export function RiskPanel({ level, probability }: { level: RiskLevel; probability: number }) {
  const meta = RISK_META[level];
  return (
    <section className={cn("rounded-md border p-5", meta.className)}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold">Riesgo actual</p>
          <p className="mt-2 text-3xl font-semibold tracking-normal">{meta.short}</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-medium">Probabilidad</p>
          <p className="mt-2 text-2xl font-semibold">{Math.round(probability * 100)}%</p>
        </div>
      </div>
    </section>
  );
}
