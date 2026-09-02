import { AlertRow } from "@/components/alerts/alert-row";
import { VitalsLineChart } from "@/components/charts/vitals-line-chart";
import { RiskPanel } from "@/components/risk/risk-badge";
import { AppShell } from "@/components/ui/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionTitle } from "@/components/ui/page-header";
import { Card, CardTitle, VitalCard } from "@/components/vitals/vital-card";
import { requireRole } from "@/lib/auth";
import { getPatientDetail } from "@/lib/data";

export default async function IpsPatientDetailPage({ params }: { params: { id: string } }) {
  await requireRole("ips");
  const { patient, vitals, prediction, report, alerts } = await getPatientDetail(params.id);
  const latest = vitals[0] ?? patient.latest_vitals ?? {};

  return (
    <AppShell role="ips" title={patient.full_name} subtitle={`${patient.city}, ${patient.department}`}>
      <div className="grid gap-5 xl:grid-cols-[340px_1fr]">
        <div className="space-y-5">
          <RiskPanel level={prediction.risk_level} probability={prediction.risk_probability} />
          <div className="grid gap-3">
            <VitalCard label="Presión" value={latest.systolic_bp && latest.diastolic_bp ? `${latest.systolic_bp}/${latest.diastolic_bp}` : "Sin dato"} unit="mmHg" />
            <VitalCard label="Pulso" value={latest.heart_rate ?? "Sin dato"} unit="lpm" />
            <VitalCard label="SpO2" value={latest.oxygen_saturation ?? "Sin dato"} unit="%" />
          </div>
        </div>
        <div className="space-y-5">
          <VitalsLineChart data={vitals} />
          <Card>
            <CardTitle>Reporte clínico</CardTitle>
            <p className="text-base leading-relaxed text-ink">{report.interpretation}</p>
            <p className="mt-3 text-base leading-relaxed text-ink">{report.recommendations}</p>
            <p className="mt-3 text-base font-semibold text-muted">{report.follow_up_actions}</p>
          </Card>
          <section>
            <SectionTitle className="mt-0">Alertas del paciente</SectionTitle>
            <div className="space-y-3">
              {alerts.length === 0 ? (
                <EmptyState>Este paciente no tiene alertas registradas.</EmptyState>
              ) : (
                alerts.map((alert) => <AlertRow key={alert.id} alert={alert} />)
              )}
            </div>
          </section>
        </div>
      </div>
    </AppShell>
  );
}
