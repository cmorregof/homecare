import { AppShell } from "@/components/ui/app-shell";
import { requireRole } from "@/lib/auth";
import { safeModelMetrics } from "@/lib/data";

export default async function AdminModelsPage() {
  await requireRole("admin");
  const models = await safeModelMetrics();

  return (
    <AppShell role="admin" title="Performance de modelos ML">
      <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
        <table className="w-full min-w-[780px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 font-semibold">Modelo</th>
              <th className="px-4 py-3 font-semibold">Estado</th>
              <th className="px-4 py-3 font-semibold">Filas</th>
              <th className="px-4 py-3 font-semibold">F1 validación</th>
              <th className="px-4 py-3 font-semibold">F1 test</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {models.map((model) => (
              <tr key={model.model}>
                <td className="px-4 py-3 font-medium text-ink">{model.model}</td>
                <td className="px-4 py-3">{model.status}</td>
                <td className="px-4 py-3">{model.train_rows_used?.toLocaleString("es-CO") ?? "Sin dato"}</td>
                <td className="px-4 py-3">{formatMetric(model.validation?.f1_macro)}</td>
                <td className="px-4 py-3">{formatMetric(model.test?.f1_macro)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </AppShell>
  );
}

function formatMetric(value?: number) {
  if (value == null) {
    return "Sin dato";
  }
  return value.toFixed(4);
}
