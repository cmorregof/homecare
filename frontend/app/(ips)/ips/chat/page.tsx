import { ChatShell } from "@/components/chat/chat-shell";
import { AppShell } from "@/components/ui/app-shell";
import { requireRole } from "@/lib/auth";
import { getIpsDashboardData } from "@/lib/data";

export default async function IpsChatPage() {
  await requireRole("ips");
  const { patients } = await getIpsDashboardData("all");
  const priority = patients[0];

  return (
    <AppShell role="ips" title="Chat clínico con Carmen">
      <ChatShell
        role="ips"
        patientId={priority?.id ?? "patient-demo-1"}
        currentRisk={priority?.latest_risk}
        latestVitals={priority?.latest_vitals}
      />
    </AppShell>
  );
}
