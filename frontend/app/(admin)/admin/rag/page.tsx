import { RagManagement } from "@/components/admin/rag-management";
import { AppShell } from "@/components/ui/app-shell";
import { requireRole } from "@/lib/auth";
import { getAdminDashboardData } from "@/lib/data";

export default async function AdminRagPage() {
  await requireRole("admin");
  const { ragDocuments } = await getAdminDashboardData();

  return (
    <AppShell role="admin" title="Gestión documentos RAG">
      <RagManagement initialDocuments={ragDocuments} />
    </AppShell>
  );
}
