import { ChatShell } from "@/components/chat/chat-shell";
import { AppShell } from "@/components/ui/app-shell";
import { requireRole } from "@/lib/auth";
import { getPatientDashboardData } from "@/lib/data";

export default async function PatientChatPage() {
  const profile = await requireRole("patient");
  const { vitals, prediction } = await getPatientDashboardData(profile.id);

  return (
    <AppShell role="patient" title="Chat con Carmen">
      <ChatShell
        role="patient"
        patientId={profile.id}
        currentRisk={prediction?.risk_level}
        latestVitals={vitals[0]}
      />
    </AppShell>
  );
}
