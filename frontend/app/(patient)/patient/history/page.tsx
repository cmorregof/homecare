import Link from "next/link";

import { AppShell } from "@/components/ui/app-shell";
import { requireRole } from "@/lib/auth";
import { getPatientHistory } from "@/lib/data";

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
      <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 font-semibold">Fecha</th>
              <th className="px-4 py-3 font-semibold">Presión</th>
              <th className="px-4 py-3 font-semibold">Pulso</th>
              <th className="px-4 py-3 font-semibold">SpO2</th>
              <th className="px-4 py-3 font-semibold">Glucosa</th>
              <th className="px-4 py-3 font-semibold">Síntomas</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row) => (
              <tr key={row.id}>
                <td className="px-4 py-3">{formatDate(row.recorded_at)}</td>
                <td className="px-4 py-3">{row.systolic_bp}/{row.diastolic_bp}</td>
                <td className="px-4 py-3">{row.heart_rate}</td>
                <td className="px-4 py-3">{row.oxygen_saturation ?? "Sin dato"}</td>
                <td className="px-4 py-3">{row.glucose ?? "Sin dato"}</td>
                <td className="px-4 py-3">Dolor {row.pain_score ?? 0}, mareo {row.dizziness_score ?? 0}, disnea {row.dyspnea_score ?? 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <div className="mt-4 flex items-center justify-between">
        <Link
          href={`/patient/history?page=${Math.max(1, page - 1)}`}
          className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700"
        >
          Anterior
        </Link>
        <p className="text-sm text-slate-600">Página {page} de {totalPages}</p>
        <Link
          href={`/patient/history?page=${Math.min(totalPages, page + 1)}`}
          className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700"
        >
          Siguiente
        </Link>
      </div>
    </AppShell>
  );
}

function formatDate(value?: string) {
  if (!value) {
    return "Sin fecha";
  }
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
