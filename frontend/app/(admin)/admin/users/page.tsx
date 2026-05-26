import { UserManagement } from "@/components/admin/user-management";
import { AppShell } from "@/components/ui/app-shell";
import { requireRole } from "@/lib/auth";
import { getAdminDashboardData } from "@/lib/data";

export default async function AdminUsersPage() {
  await requireRole("admin");
  const { profiles } = await getAdminDashboardData();

  return (
    <AppShell role="admin" title="Gestión de usuarios">
      <UserManagement initialProfiles={profiles} />
    </AppShell>
  );
}
