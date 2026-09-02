import { AlertOctagon, AlertTriangle, ShieldCheck, Siren, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/types";

/**
 * Risk tiers, following the reference `.badge` / `.chip` shape
 * (proyecto_daniela @ 1aa2b0a — global.css:378-390: pill, 999px radius,
 * 12px, weight 700) but carrying four tiers where the reference has none.
 *
 * WHY THE TIERS DO NOT DIFFER BY COLOUR ALONE
 *
 * `risk.high` (#C62828) and `risk.critical` (#9A0007) are both dark reds:
 * 1.57:1 against each other, and closer still under deuteranopia. A viewer
 * who cannot separate those two hues would be unable to tell a high-risk
 * patient from a critical one — the single most consequential distinction
 * in the product.
 *
 * So each tier differs on four channels at once:
 *
 *   tier      fill                 text    border      weight  icon
 *   low       risk.low at 8%       green   —           600     ShieldCheck
 *   moderate  risk.moderate solid  ink     —           600     AlertTriangle
 *   high      surface (white)      red     2px red     700     AlertOctagon
 *   critical  risk.critical solid  white   —           800     Siren + pulse
 *
 * Read as greyscale the fills ramp light → mid → white-with-ring → very dark,
 * and the text/fill polarity inverts twice, so the ordering survives with no
 * hue information at all. Every combination clears WCAG AA for normal text:
 * 4.63 / 4.72 / 5.62 / 8.83:1 respectively. `high` and `critical` — the pair
 * that colour cannot separate — sit 8.83:1 apart as treatments.
 */
type RiskMeta = {
  label: string;
  short: string;
  icon: LucideIcon;
  /** Badge surface: fill, text, border and weight. */
  badge: string;
  /** Same treatment at panel scale. */
  panel: string;
  /** Accent for icons rendered outside a badge. */
  accent: string;
};

export const RISK_META: Record<RiskLevel, RiskMeta> = {
  low: {
    label: "Bajo",
    short: "BAJO",
    icon: ShieldCheck,
    badge: "border border-transparent bg-risk-low/[0.08] font-semibold text-risk-low",
    panel: "border border-risk-low/30 bg-risk-low/[0.08] text-risk-low",
    accent: "text-risk-low",
  },
  moderate: {
    label: "Moderado",
    short: "MODERADO",
    icon: AlertTriangle,
    badge: "border border-transparent bg-risk-moderate font-semibold text-ink",
    panel: "border border-risk-moderate bg-risk-moderate text-ink",
    accent: "text-risk-moderate",
  },
  high: {
    label: "Alto",
    short: "ALTO",
    icon: AlertOctagon,
    badge: "border-2 border-risk-high bg-surface font-bold text-risk-high",
    panel: "border-2 border-risk-high bg-surface text-risk-high",
    accent: "text-risk-high",
  },
  critical: {
    label: "Crítico",
    short: "CRÍTICO",
    icon: Siren,
    badge: "border border-transparent bg-risk-critical font-extrabold text-white",
    panel: "border border-transparent bg-risk-critical text-white",
    accent: "text-risk-critical",
  },
};

export function RiskBadge({ level, compact = false }: { level: RiskLevel; compact?: boolean }) {
  const meta = RISK_META[level];
  const Icon = meta.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs uppercase tracking-[0.04em]",
        meta.badge,
      )}
    >
      <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden />
      {compact ? meta.short : meta.label}
      {level === "critical" ? (
        <span className="relative flex h-1.5 w-1.5" aria-hidden>
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white opacity-75" />
          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-white" />
        </span>
      ) : null}
      <span className="sr-only">Nivel de riesgo: {meta.label}</span>
    </span>
  );
}

export function RiskPanel({ level, probability }: { level: RiskLevel; probability: number }) {
  const meta = RISK_META[level];
  const Icon = meta.icon;
  return (
    <section className={cn("rounded-lg p-6 shadow-sm", meta.panel)}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.06em] opacity-90">
            <Icon className="h-4 w-4 shrink-0" aria-hidden />
            Riesgo actual
          </p>
          <p className="mt-2 text-4xl font-bold">{meta.short}</p>
        </div>
        <div className="text-right">
          <p className="text-xs font-semibold uppercase tracking-[0.06em] opacity-90">Probabilidad</p>
          <p className="mt-2 text-3xl font-bold">{Math.round(probability * 100)}%</p>
        </div>
      </div>
    </section>
  );
}
