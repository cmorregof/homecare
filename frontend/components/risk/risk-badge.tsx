import { RiskLevel } from "@/types";

const RISK_LABELS: Record<RiskLevel, string> = {
  low: "🟢 BAJO",
  moderate: "🟡 MODERADO",
  high: "🔴 ALTO",
  critical: "🚨 CRÍTICO",
};

export function RiskBadge({ level }: { level: RiskLevel }) {
  return <span className="rounded-md border border-slate-200 bg-white px-3 py-1 text-sm">{RISK_LABELS[level]}</span>;
}
