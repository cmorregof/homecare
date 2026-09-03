import Link from "next/link";

import { AlertRow } from "@/components/alerts/alert-row";
import { RiskBadge } from "@/components/risk/risk-badge";
import { AppShell } from "@/components/ui/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { MetricCard, MetricGrid } from "@/components/ui/metric-card";
import { SectionTitle } from "@/components/ui/page-header";
import { Table, TableWrap, Td, Th, Tr } from "@/components/ui/table";
import { cn, formatClinical } from "@/lib/utils";
import { requireRole } from "@/lib/auth";
import { getIpsDashboardData } from "@/lib/data";
import type { RiskLevel } from "@/types";

const FILTERS = ["all", "critical", "high", "moderate", "low"] as const;

export default async function IpsDashboardPage({
  searchParams,
}: {
  searchParams?: { risk?: RiskLevel | "all" };
}) {
  const viewer = await requireRole("ips");
  const active = searchParams?.risk ?? "all";
  const { patients, alerts } = await getIpsDashboardData(active);
  const critical = patients.filter((patient) => patient.latest_risk === "critical").length;
  const high = patients.filter((patient) => patient.latest_risk === "high").length;

  return (
    <AppShell role="ips" title="Dashboard IPS" subtitle="Pacientes priorizados por riesgo clínico" userName={viewer.full_name}>
      <MetricGrid>
        <MetricCard label="Pacientes activos" value={patients.length} tone="featured" detail="Bajo seguimiento" />
        <MetricCard label="Críticos" value={critical} tone="danger" />
        <MetricCard label="Alto riesgo" value={high} tone="warning" />
        <MetricCard label="Alertas abiertas" value={alerts.filter((alert) => !alert.acknowledged).length} />
      </MetricGrid>

      <TableWrap>
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
          <h2 className="text-lg font-bold text-ink">Pacientes</h2>
          {/* The reference's `.chips` / `.chip.active` (global.css:319-334). */}
          <div className="flex flex-wrap gap-2">
            {FILTERS.map((risk) => {
              const current = risk === active;
              return (
                <Link
                  key={risk}
                  href={`/ips/dashboard?risk=${risk}`}
                  aria-current={current ? "true" : undefined}
                  className={cn(
                    "rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors",
                    "outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2",
                    current
                      ? "border-brand bg-brand text-white"
                      : "border-border bg-surface text-ink hover:bg-canvas",
                  )}
                >
                  {filterLabel(risk)}
                </Link>
              );
            })}
          </div>
        </div>
        {patients.length === 0 ? (
          <EmptyState>No hay pacientes para este filtro.</EmptyState>
        ) : (
          <div className="min-w-[860px]">
            <Table>
              <thead>
                <tr>
                  <Th>Paciente</Th>
                  <Th>Riesgo</Th>
                  <Th>Presión</Th>
                  <Th>Tendencia</Th>
                  <Th>Último reporte</Th>
                </tr>
              </thead>
              <tbody>
                {patients.map((patient) => (
                  <Tr key={patient.id}>
                    <Td>
                      <Link
                        href={`/ips/patients/${patient.id}`}
                        className="font-semibold text-brand outline-none hover:underline focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2"
                      >
                        {patient.full_name}
                      </Link>
                      <p className="text-xs text-muted">{patient.city}</p>
                    </Td>
                    <Td><RiskBadge level={patient.latest_risk} compact /></Td>
                    <Td>{patient.latest_vitals?.systolic_bp}/{patient.latest_vitals?.diastolic_bp}</Td>
                    <Td><Trend levels={patient.trend} /></Td>
                    <Td>{formatDate(patient.last_report_at)}</Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          </div>
        )}
      </TableWrap>

      <div className="mt-6 flex items-center justify-between">
        <SectionTitle className="mt-0">Alertas recientes</SectionTitle>
        <Link
          href="/ips/alerts"
          className="text-sm font-semibold text-brand outline-none hover:underline focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2"
        >
          Centro de alertas
        </Link>
      </div>
      <div className="space-y-3">
        {alerts.length === 0 ? (
          <EmptyState>Sin alertas recientes.</EmptyState>
        ) : (
          alerts.slice(0, 3).map((alert) => <AlertRow key={alert.id} alert={alert} />)
        )}
      </div>
    </AppShell>
  );
}

/**
 * Recent risk history.
 *
 * Severity is carried by BAR HEIGHT as well as colour. The previous version
 * used five equal blocks that differed only in hue, and the two red tiers
 * collapsed into one another under deuteranopia — the same defect the risk
 * badge was rebuilt to avoid, one component further out.
 */
const TREND: Record<RiskLevel, { fill: string; height: string }> = {
  low: { fill: "bg-risk-low", height: "h-2" },
  moderate: { fill: "bg-risk-moderate", height: "h-4" },
  high: { fill: "bg-risk-high", height: "h-6" },
  critical: { fill: "bg-risk-critical", height: "h-8" },
};

function Trend({ levels }: { levels: RiskLevel[] }) {
  return (
    <div className="flex h-8 items-end gap-1" role="img" aria-label={trendLabel(levels)}>
      {levels.map((level, index) => (
        <span
          key={`${index}-${level}`}
          className={cn("w-8 rounded-sm", TREND[level].fill, TREND[level].height)}
        />
      ))}
    </div>
  );
}

function trendLabel(levels: RiskLevel[]) {
  return `Tendencia de riesgo: ${levels.map((level) => filterLabel(level)).join(", ")}`;
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
  return formatClinical(value, { month: "short", day: "2-digit", hour: "2-digit" });
}
