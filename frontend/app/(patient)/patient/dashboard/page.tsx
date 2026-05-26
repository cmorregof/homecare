import Link from "next/link";
import { MessageCircle, Send } from "lucide-react";

import { VitalsLineChart } from "@/components/charts/vitals-line-chart";
import { RiskPanel } from "@/components/risk/risk-badge";
import { AppShell } from "@/components/ui/app-shell";
import { VitalCard } from "@/components/vitals/vital-card";
import { requireRole } from "@/lib/auth";
import { getPatientDashboardData } from "@/lib/data";

const TELEGRAM_URL = process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ?? "https://t.me/project918_homecare_bot";

export default async function PatientDashboardPage() {
  await requireRole("patient");
  const { profile, vitals, prediction, report } = await getPatientDashboardData();
  const latest = vitals[0] ?? {};
  const riskLevel = prediction?.risk_level ?? "low";
  const probability = prediction?.risk_probability ?? 0;

  return (
    <AppShell role="patient" title="Panel del paciente" subtitle={profile?.full_name ?? "Paciente"}>
      <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
        <div className="space-y-5">
          <RiskPanel level={riskLevel} probability={probability} />
          <section className="rounded-md border border-slate-200 bg-white p-5">
            <h2 className="text-base font-semibold">Recomendación médica</h2>
            <p className="mt-3 text-sm leading-6 text-slate-700">
              {report?.recommendations ?? "Aún no hay recomendaciones clínicas registradas."}
            </p>
            <p className="mt-3 text-sm font-medium text-slate-600">{report?.follow_up_actions}</p>
          </section>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <Link
              href={TELEGRAM_URL}
              className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-clinical px-4 text-sm font-medium text-white transition hover:bg-teal-800"
            >
              <Send className="h-4 w-4" aria-hidden />
              Registrar en Telegram
            </Link>
            <Link
              href="/patient/chat"
              className="inline-flex h-11 items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-4 text-sm font-medium text-slate-800 transition hover:bg-slate-100"
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
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-base font-semibold">Últimas mediciones</h2>
              <Link href="/patient/history" className="text-sm font-medium text-clinical">Ver historial</Link>
            </div>
            <VitalsLineChart data={vitals} />
          </section>
        </div>
      </div>
    </AppShell>
  );
}
