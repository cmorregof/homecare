import { CheckCircle2, Clock } from "lucide-react";

import { RiskBadge } from "@/components/risk/risk-badge";
import type { AlertRecord } from "@/types";

export function AlertRow({ alert }: { alert: AlertRecord }) {
  return (
    <article className="grid gap-3 rounded-md border border-slate-200 bg-white p-4 md:grid-cols-[160px_1fr_160px]">
      <div>
        <RiskBadge level={alert.risk_level} compact />
        <p className="mt-2 text-xs text-slate-500">{formatDate(alert.created_at)}</p>
      </div>
      <div>
        <p className="font-medium text-ink">{alert.patient_name ?? alert.patient_id}</p>
        <p className="mt-1 text-sm leading-6 text-slate-600">{alert.message}</p>
      </div>
      <div className="flex items-center gap-2 text-sm text-slate-600 md:justify-end">
        {alert.acknowledged ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <Clock className="h-4 w-4 text-amber-600" />}
        {alert.acknowledged ? "Atendida" : "Pendiente"}
      </div>
    </article>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es-CO", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
