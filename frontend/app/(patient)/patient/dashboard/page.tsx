import Link from "next/link";
import { MessageCircle, Plus, Send } from "lucide-react";

import { VitalsLineChart } from "@/components/charts/vitals-line-chart";
import { RiskPanel } from "@/components/risk/risk-badge";
import { AppShell } from "@/components/ui/app-shell";
import { SectionTitle } from "@/components/ui/page-header";
import { WelcomeBanner } from "@/components/ui/welcome-banner";
import { Card, CardTitle, VitalCard } from "@/components/vitals/vital-card";
import { requireRole } from "@/lib/auth";
import { getPatientDashboardData } from "@/lib/data";
import { cn } from "@/lib/utils";

const TELEGRAM_URL = process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ?? "https://t.me/project918_homecare_bot";

/** Link styled as a button. Mirrors components/ui/button.tsx for anchors. */
const LINK_BUTTON = cn(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md border px-[18px] py-2.5 text-base font-semibold transition",
  "outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-surface",
  "active:translate-y-px",
);

export default async function PatientDashboardPage() {
  await requireRole("patient");
  const { profile, vitals, prediction, report } = await getPatientDashboardData();
  const latest = vitals[0] ?? {};
  const riskLevel = prediction?.risk_level ?? "low";
  const probability = prediction?.risk_probability ?? 0;

  return (
    <AppShell
      role="patient"
      title="Panel del paciente"
      subtitle={profile?.full_name ?? "Paciente"}
      actions={
        <Link href="/patient/vitals/new" className={cn(LINK_BUTTON, "border-transparent bg-brand text-white hover:opacity-[0.92]")}>
          <Plus className="h-4 w-4" aria-hidden />
          Nueva medición
        </Link>
      }
    >
      <WelcomeBanner />
      <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
        <div className="space-y-5">
          <RiskPanel level={riskLevel} probability={probability} />
          <Card>
            <CardTitle>Recomendación médica</CardTitle>
            <p className="text-base leading-relaxed text-ink">
              {report?.recommendations ?? "Aún no hay recomendaciones clínicas registradas."}
            </p>
            {report?.follow_up_actions ? (
              <p className="mt-3 text-base font-semibold text-muted">{report.follow_up_actions}</p>
            ) : null}
          </Card>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <Link
              href={TELEGRAM_URL}
              className={cn(LINK_BUTTON, "border-transparent bg-brand text-white hover:opacity-[0.92]")}
            >
              <Send className="h-4 w-4" aria-hidden />
              Registrar en Telegram
            </Link>
            <Link
              href="/patient/chat"
              className={cn(LINK_BUTTON, "border-border bg-surface text-ink hover:bg-canvas")}
            >
              <MessageCircle className="h-4 w-4" aria-hidden />
              Chat con Carmen
            </Link>
          </div>
        </div>

        <div className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <VitalCard label="Presión arterial" value={latest.systolic_bp && latest.diastolic_bp ? `${latest.systolic_bp}/${latest.diastolic_bp}` : "Sin dato"} unit="mmHg" />
            <VitalCard label="Frecuencia cardíaca" value={latest.heart_rate ?? "Sin dato"} unit="lpm" />
            <VitalCard label="Saturación O2" value={latest.oxygen_saturation ?? "Sin dato"} unit="%" />
            <VitalCard label="Glucosa" value={latest.glucose ?? "Sin dato"} unit="mg/dL" />
          </div>
          <section>
            <div className="flex items-center justify-between">
              <SectionTitle className="mt-0">Últimas mediciones</SectionTitle>
              <Link
                href="/patient/history"
                className="text-sm font-semibold text-brand outline-none hover:underline focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2"
              >
                Ver historial
              </Link>
            </div>
            <VitalsLineChart data={vitals} />
          </section>
        </div>
      </div>
    </AppShell>
  );
}
