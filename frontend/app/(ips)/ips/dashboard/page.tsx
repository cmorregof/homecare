import Link from "next/link";

import { AlertRow } from "@/components/alerts/alert-row";
import { RiskBadge } from "@/components/risk/risk-badge";
import { AppShell } from "@/components/ui/app-shell";
import { MetricCard } from "@/components/ui/metric-card";
import { requireRole } from "@/lib/auth";
import { getIpsDashboardData } from "@/lib/data";
import type { RiskLevel } from "@/types";

export default async function IpsDashboardPage({
  searchParams,
}: {
  searchParams?: { risk?: RiskLevel | "all" };
}) {
  await requireRole("ips");
  const { patients, alerts } = await getIpsDashboardData(searchParams?.risk ?? "all");
  const critical = patients.filter((patient) => patient.latest_risk === "critical").length;
  const high = patients.filter((patient) => patient.latest_risk === "high").length;

  return (
    <AppShell role="ips" title="Dashboard IPS" subtitle="Pacientes priorizados por riesgo clínico">
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Pacientes activos" value={patients.length} />
        <MetricCard label="Críticos" value={critical} tone="danger" />
        <MetricCard label="Alto riesgo" value={high} tone="warning" />
        <MetricCard label="Alertas abiertas" value={alerts.filter((alert) => !alert.acknowledged).length} />
      </div>

      <section className="mt-6 rounded-md border border-slate-200 bg-white">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3">
          <h2 className="font-semibold">Pacientes</h2>
          <div className="flex flex-wrap gap-2">
            {(["all", "critical", "high", "moderate", "low"] as const).map((risk) => (
              <Link key={risk} href={`/ips/dashboard?risk=${risk}`} className="rounded-md border border-slate-200 px-3 py-1.5 text-sm font-medium">
                {filterLabel(risk)}
              </Link>
            ))}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3 font-semibold">Paciente</th>
                <th className="px-4 py-3 font-semibold">Riesgo</th>
                <th className="px-4 py-3 font-semibold">Presión</th>
                <th className="px-4 py-3 font-semibold">Tendencia</th>
                <th className="px-4 py-3 font-semibold">Último reporte</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {patients.map((patient) => (
                <tr key={patient.id}>
                  <td className="px-4 py-3">
                    <Link href={`/ips/patients/${patient.id}`} className="font-medium text-clinical">
                      {patient.full_name}
                    </Link>
                    <p className="text-xs text-slate-500">{patient.city}</p>
                  </td>
                  <td className="px-4 py-3"><RiskBadge level={patient.latest_risk} compact /></td>
                  <td className="px-4 py-3">{patient.latest_vitals?.systolic_bp}/{patient.latest_vitals?.diastolic_bp}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {patient.trend.map((level, index) => (
                        <span key={`${patient.id}-${index}`} className={heatClass(level)} />
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">{formatDate(patient.last_report_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">Alertas recientes</h2>
          <Link href="/ips/alerts" className="text-sm font-medium text-clinical">Centro de alertas</Link>
        </div>
        <div className="space-y-3">
          {alerts.slice(0, 3).map((alert) => (
            <AlertRow key={alert.id} alert={alert} />
          ))}
        </div>
      </section>
    </AppShell>
  );
}

function heatClass(level: RiskLevel) {
  const colors: Record<RiskLevel, string> = {
    low: "bg-emerald-400",
    moderate: "bg-amber-400",
    high: "bg-red-500",
    critical: "bg-rose-700",
  };
  return `h-6 w-8 rounded-sm ${colors[level]}`;
}

function filterLabel(value: RiskLevel | "all") {
  const labels = {
    all: "Todos",
    critical: "Crítico",
    high: "Alto",
    moderate: "Moderado",
    low: "Bajo",
  };
  return labels[value];
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es-CO", { month: "short", day: "2-digit", hour: "2-digit" }).format(new Date(value));
}
