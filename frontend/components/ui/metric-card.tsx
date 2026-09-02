import { cn } from "@/lib/utils";

/**
 * KPI tile, ported from the reference `.kpi` / `.kpi-grid`
 * (proyecto_daniela @ 1aa2b0a — global.css:428-462): surface, 20px padding,
 * radius-lg, 1px border, shadow-sm; label 12px uppercase muted 600 with
 * 0.04em tracking; value 30px/700; trend 12px muted.
 *
 * The reference has one variant (`.kpi.primary`, a red gradient). Ours carries
 * a `tone` instead, because these tiles count patients by risk tier and the
 * tint has to agree with the risk palette rather than with the brand.
 */
const TONES = {
  neutral: "border-border bg-surface",
  good: "border-risk-low/30 bg-risk-low/[0.08]",
  warning: "border-risk-moderate/40 bg-risk-moderate/10",
  danger: "border-risk-high/30 bg-risk-high/[0.08]",
} as const;

export function MetricCard({
  label,
  value,
  detail,
  tone = "neutral",
}: {
  label: string;
  value: string | number;
  detail?: string;
  tone?: keyof typeof TONES;
}) {
  return (
    <div className={cn("rounded-lg border p-5 shadow-sm", TONES[tone])}>
      <p className="text-xs font-semibold uppercase tracking-[0.04em] text-muted">{label}</p>
      <p className="mt-1.5 text-4xl font-bold text-ink">{value}</p>
      {detail ? <p className="mt-1 text-xs text-muted">{detail}</p> : null}
    </div>
  );
}

/** The reference's `.kpi-grid`: auto-fit columns with a 200px floor. */
export function MetricGrid({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-6 grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">{children}</div>
  );
}
