import Link from "next/link";

import { AppShell } from "@/components/ui/app-shell";
import { MetricCard, MetricGrid } from "@/components/ui/metric-card";
import { Card, CardTitle } from "@/components/vitals/vital-card";
import { requireRole } from "@/lib/auth";
import { getAdminDashboardData } from "@/lib/data";

const CARD_LINK =
  "text-sm font-semibold text-brand outline-none hover:underline focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2";

export default async function AdminDashboardPage() {
  await requireRole("admin");
  const { metrics, modelMetrics, ragDocuments } = await getAdminDashboardData();
  const bestModel = [...modelMetrics].sort((a, b) => (b.validation?.f1_macro ?? 0) - (a.validation?.f1_macro ?? 0))[0];

  return (
    <AppShell role="admin" title="Métricas del sistema">
      <MetricGrid>
        <MetricCard label="Pacientes" value={metrics.totalPatients} />
        <MetricCard label="Reportes hoy" value={metrics.reportsToday} />
        <MetricCard label="Alertas hoy" value={metrics.alertsToday} tone="warning" />
        <MetricCard label="Críticas" value={metrics.criticalAlerts} tone="danger" />
      </MetricGrid>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card>
          <div className="flex items-center justify-between">
            <CardTitle>Modelo líder</CardTitle>
            <Link href="/admin/models" className={CARD_LINK}>Ver modelos</Link>
          </div>
          <p className="text-4xl font-bold text-ink">{bestModel?.model ?? "Sin modelo"}</p>
          <p className="mt-2 text-base text-muted">F1 macro validación {formatPercent(bestModel?.validation?.f1_macro)}</p>
        </Card>
        <Card>
          <div className="flex items-center justify-between">
            <CardTitle>Documentos RAG</CardTitle>
            <Link href="/admin/rag" className={CARD_LINK}>Gestionar</Link>
          </div>
          <p className="text-4xl font-bold text-ink">{ragDocuments.length}</p>
          <p className="mt-2 text-base text-muted">Fuentes clínicas indexadas o listas para indexar</p>
        </Card>
      </div>
    </AppShell>
  );
}

function formatPercent(value?: number) {
  if (value == null) {
    return "sin dato";
  }
  return `${(value * 100).toFixed(1)}%`;
}
