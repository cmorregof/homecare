import { RealtimeAlertList } from "@/components/alerts/realtime-alert-list";
import { AppShell } from "@/components/ui/app-shell";
import { requireRole } from "@/lib/auth";
import { getIpsDashboardData } from "@/lib/data";

export default async function IpsAlertsPage() {
  const viewer = await requireRole("ips");
  const { alerts } = await getIpsDashboardData("all");

  return (
    <AppShell role="ips" title="Centro de alertas" subtitle="Actualización en tiempo real cuando Supabase Realtime está activo" userName={viewer.full_name}>
      <RealtimeAlertList initialAlerts={alerts} />
    </AppShell>
  );
}
