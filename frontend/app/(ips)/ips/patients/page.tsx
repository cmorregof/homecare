import Link from "next/link";
import { Search } from "lucide-react";

import { RiskBadge } from "@/components/risk/risk-badge";
import { AppShell } from "@/components/ui/app-shell";
import { requireRole } from "@/lib/auth";
import { getIpsDashboardData } from "@/lib/data";

export default async function IpsPatientsPage() {
  await requireRole("ips");
  const { patients } = await getIpsDashboardData("all");

  return (
    <AppShell role="ips" title="Pacientes asignados">
      <section className="rounded-md border border-slate-200 bg-white">
        <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3">
          <Search className="h-4 w-4 text-slate-500" aria-hidden />
          <input className="h-10 flex-1 outline-none" placeholder="Buscar paciente" />
        </div>
        <div className="divide-y divide-slate-100">
          {patients.map((patient) => (
            <Link key={patient.id} href={`/ips/patients/${patient.id}`} className="grid gap-3 px-4 py-4 transition hover:bg-slate-50 md:grid-cols-[1fr_180px_160px]">
              <div>
                <p className="font-medium text-ink">{patient.full_name}</p>
                <p className="text-sm text-slate-600">{patient.document_id} · {patient.city}</p>
              </div>
              <RiskBadge level={patient.latest_risk} />
              <p className="text-sm text-slate-600">Prob. {Math.round(patient.latest_probability * 100)}%</p>
            </Link>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
