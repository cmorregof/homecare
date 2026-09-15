import Link from "next/link";
import { Search } from "lucide-react";

import { RiskBadge } from "@/components/risk/risk-badge";
import { AppShell } from "@/components/ui/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { TableWrap } from "@/components/ui/table";
import { requireRole } from "@/lib/auth";
import { getIpsDashboardData } from "@/lib/data";

export default async function IpsPatientsPage() {
  const viewer = await requireRole("ips");
  const { patients } = await getIpsDashboardData("all");

  return (
    <AppShell role="ips" title="Pacientes asignados" userName={viewer.full_name}>
      <TableWrap>
        <div className="flex items-center gap-2 border-b border-border px-4 py-3">
          <Search className="h-4 w-4 shrink-0 text-muted" aria-hidden />
          <label htmlFor="patient-search" className="sr-only">
            Buscar paciente
          </label>
          {/* NOTE: decorative today — this input is not wired to any query. */}
          <input
            id="patient-search"
            className="min-w-0 flex-1 bg-transparent py-1.5 text-base text-ink outline-none placeholder:text-muted"
            placeholder="Buscar paciente"
          />
        </div>
        {patients.length === 0 ? (
          <EmptyState>No hay pacientes asignados.</EmptyState>
        ) : (
          <div>
            {patients.map((patient) => (
              <Link
                key={patient.id}
                href={`/ips/patients/${patient.id}`}
                className="grid items-center gap-3 border-b border-border px-4 py-4 transition-colors last:border-b-0 hover:bg-brand-soft md:grid-cols-[1fr_180px_160px] outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-inset"
              >
                <div>
                  <p className="font-semibold text-ink">{patient.full_name}</p>
                  <p className="text-sm text-muted">{patient.document_id} · {patient.city}</p>
                </div>
                <RiskBadge level={patient.latest_risk} />
                <p className="text-sm text-muted">Prob. {Math.round(patient.latest_probability * 100)}%</p>
              </Link>
            ))}
          </div>
        )}
      </TableWrap>
    </AppShell>
  );
}
