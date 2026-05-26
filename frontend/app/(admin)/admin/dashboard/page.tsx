import Link from "next/link";

import { AppShell } from "@/components/ui/app-shell";
import { MetricCard } from "@/components/ui/metric-card";
import { requireRole } from "@/lib/auth";
import { getAdminDashboardData } from "@/lib/data";

export default async function AdminDashboardPage() {
  await requireRole("admin");
  const { metrics, modelMetrics, ragDocuments } = await getAdminDashboardData();
  const bestModel = [...modelMetrics].sort((a, b) => (b.validation?.f1_macro ?? 0) - (a.validation?.f1_macro ?? 0))[0];

  return (
    <AppShell role="admin" title="Métricas del sistema">
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Pacientes" value={metrics.totalPatients} />
        <MetricCard label="Reportes hoy" value={metrics.reportsToday} />
        <MetricCard label="Alertas hoy" value={metrics.alertsToday} tone="warning" />
        <MetricCard label="Críticas" value={metrics.criticalAlerts} tone="danger" />
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <section className="rounded-md border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Modelo líder</h2>
            <Link href="/admin/models" className="text-sm font-medium text-clinical">Ver modelos</Link>
          </div>
          <p className="mt-4 text-3xl font-semibold tracking-normal">{bestModel?.model ?? "Sin modelo"}</p>
          <p className="mt-2 text-sm text-slate-600">F1 macro validación {formatPercent(bestModel?.validation?.f1_macro)}</p>
        </section>
        <section className="rounded-md border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Documentos RAG</h2>
            <Link href="/admin/rag" className="text-sm font-medium text-clinical">Gestionar</Link>
          </div>
          <p className="mt-4 text-3xl font-semibold tracking-normal">{ragDocuments.length}</p>
          <p className="mt-2 text-sm text-slate-600">Fuentes clínicas indexadas o listas para indexar</p>
        </section>
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
