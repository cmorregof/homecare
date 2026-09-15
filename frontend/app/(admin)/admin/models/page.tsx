import { AppShell } from "@/components/ui/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { Table, TableWrap, Td, Th, Tr } from "@/components/ui/table";
import { requireRole } from "@/lib/auth";
import { safeModelMetrics } from "@/lib/data";

export default async function AdminModelsPage() {
  const viewer = await requireRole("admin");
  const models = await safeModelMetrics();

  return (
    <AppShell role="admin" title="Performance de modelos ML" userName={viewer.full_name}>
      <TableWrap>
        {models.length === 0 ? (
          <EmptyState>No hay métricas de modelos disponibles.</EmptyState>
        ) : (
          <div className="min-w-[780px]">
            <Table>
              <thead>
                <tr>
                  <Th>Modelo</Th>
                  <Th>Estado</Th>
                  <Th>Filas</Th>
                  <Th>F1 validación</Th>
                  <Th>F1 test</Th>
                </tr>
              </thead>
              <tbody>
                {models.map((model) => (
                  <Tr key={model.model}>
                    <Td className="font-semibold text-ink">{model.model}</Td>
                    <Td className="text-muted">{model.status}</Td>
                    <Td>{model.train_rows_used?.toLocaleString("es-CO") ?? "Sin dato"}</Td>
                    <Td>{formatMetric(model.validation?.f1_macro)}</Td>
                    <Td>{formatMetric(model.test?.f1_macro)}</Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          </div>
        )}
      </TableWrap>
    </AppShell>
  );
}

function formatMetric(value?: number) {
  if (value == null) {
    return "Sin dato";
  }
  return value.toFixed(4);
}
