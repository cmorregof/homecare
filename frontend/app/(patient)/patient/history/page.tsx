import Link from "next/link";

import { AppShell } from "@/components/ui/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { Table, TableWrap, Td, Th, Tr } from "@/components/ui/table";
import { requireRole } from "@/lib/auth";
import { getPatientHistory } from "@/lib/data";
import { cn, formatClinical } from "@/lib/utils";

const PAGER = cn(
  "inline-flex items-center rounded-md border border-border bg-surface px-3.5 py-2 text-base font-semibold text-ink transition-colors hover:bg-canvas",
  "outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2",
  "aria-disabled:pointer-events-none aria-disabled:opacity-50",
);

export default async function PatientHistoryPage({
  searchParams,
}: {
  searchParams?: { page?: string };
}) {
  await requireRole("patient");
  const page = Math.max(1, Number(searchParams?.page ?? "1"));
  const { rows, total, pageSize } = await getPatientHistory(page);
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <AppShell role="patient" title="Historial de signos vitales">
      <TableWrap>
        {rows.length === 0 ? (
          <EmptyState>Todavía no hay mediciones registradas.</EmptyState>
        ) : (
          <div className="min-w-[760px]">
            <Table>
              <thead>
                <tr>
                  <Th>Fecha</Th>
                  <Th>Presión</Th>
                  <Th>Pulso</Th>
                  <Th>SpO2</Th>
                  <Th>Glucosa</Th>
                  <Th>Síntomas</Th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <Tr key={row.id}>
                    <Td>{formatDate(row.recorded_at)}</Td>
                    <Td>{row.systolic_bp}/{row.diastolic_bp}</Td>
                    <Td>{row.heart_rate}</Td>
                    <Td>{row.oxygen_saturation ?? "Sin dato"}</Td>
                    <Td>{row.glucose ?? "Sin dato"}</Td>
                    <Td className="text-muted">
                      Dolor {row.pain_score ?? 0}, mareo {row.dizziness_score ?? 0}, disnea {row.dyspnea_score ?? 0}
                    </Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          </div>
        )}
      </TableWrap>
      <nav className="mt-4 flex items-center justify-between" aria-label="Paginación del historial">
        <Link
          href={`/patient/history?page=${Math.max(1, page - 1)}`}
          aria-disabled={page <= 1}
          className={PAGER}
        >
          Anterior
        </Link>
        <p className="text-base text-muted">Página {page} de {totalPages}</p>
        <Link
          href={`/patient/history?page=${Math.min(totalPages, page + 1)}`}
          aria-disabled={page >= totalPages}
          className={PAGER}
        >
          Siguiente
        </Link>
      </nav>
    </AppShell>
  );
}

function formatDate(value?: string) {
  if (!value) {
    return "Sin fecha";
  }
  return formatClinical(value, { dateStyle: "medium", timeStyle: "short" });
}
