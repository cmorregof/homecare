import { CheckCircle2, Clock } from "lucide-react";

import { RISK_META, RiskBadge } from "@/components/risk/risk-badge";
import { cn, formatClinical } from "@/lib/utils";
import type { AlertRecord } from "@/types";

/**
 * Flash banner, ported from the reference `.alert`
 * (proyecto_daniela @ 1aa2b0a — global.css:370-376): 12px/16px padding,
 * radius-md, 14px, tinted by outcome.
 */
export function Alert({ tone, children }: { tone: "error" | "success"; children: React.ReactNode }) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "mb-4 rounded-md border px-4 py-3 text-base",
        tone === "error"
          ? "border-danger/40 bg-danger/[0.08] text-danger"
          : "border-success/40 bg-success/[0.08] text-success",
      )}
    >
      {children}
    </div>
  );
}

/**
 * A clinical alert about a patient. This one has no precedent in the
 * reference — its `.alert` is a flash message, not a per-patient record — so
 * the language is extended rather than copied: the `.card` surface (radius-lg,
 * 1px border, shadow-sm) carrying a risk tier.
 *
 * The tier is signalled three ways: the left edge, the badge, and the badge's
 * icon. That edge is the reason the row is readable in a dense list at a
 * glance without relying on the badge's fill alone.
 */
export function AlertRow({ alert }: { alert: AlertRecord }) {
  const meta = RISK_META[alert.risk_level];
  return (
    <article
      className={cn(
        "grid gap-3 rounded-lg border border-border bg-surface p-5 shadow-sm md:grid-cols-[170px_1fr_150px]",
        "border-l-4",
        EDGE[alert.risk_level],
      )}
    >
      <div>
        <RiskBadge level={alert.risk_level} compact />
        <p className="mt-2 text-xs text-muted">{formatDate(alert.created_at)}</p>
      </div>
      <div>
        <p className="font-semibold text-ink">{alert.patient_name ?? alert.patient_id}</p>
        <p className="mt-1 text-base leading-relaxed text-muted">{alert.message}</p>
      </div>
      <div className="flex items-center gap-2 text-base text-muted md:justify-end">
        {alert.acknowledged ? (
          <CheckCircle2 className={cn("h-4 w-4 shrink-0", "text-success")} aria-hidden />
        ) : (
          <Clock className={cn("h-4 w-4 shrink-0", meta.accent)} aria-hidden />
        )}
        {alert.acknowledged ? "Atendida" : "Pendiente"}
      </div>
    </article>
  );
}

/** Left severity edge. Written out so Tailwind keeps each class. */
const EDGE: Record<AlertRecord["risk_level"], string> = {
  low: "border-l-risk-low",
  moderate: "border-l-risk-moderate",
  high: "border-l-risk-high",
  critical: "border-l-risk-critical",
};

function formatDate(value: string) {
  return formatClinical(value, { month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}
