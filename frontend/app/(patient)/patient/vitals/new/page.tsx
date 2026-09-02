import { AppShell } from "@/components/ui/app-shell";
import { VitalReportForm } from "@/components/vitals/vital-report-form";
import { requireRole } from "@/lib/auth";

/**
 * Web capture for a vitals report.
 *
 * NOTE ON THE PATH. The work order placed this at `app/(patient)/vitals/new`,
 * which Next.js resolves to the URL `/vitals/new`. The middleware matcher only
 * covers `/patient/:path*`, `/ips/:path*` and `/admin/:path*`
 * (middleware.ts:84), so that URL would have shipped with no role gate at all —
 * a form that writes patient vitals, reachable while signed out. It lives under
 * `/patient/vitals/new` instead, inside the matcher, alongside the other
 * patient routes.
 */
export default async function NewVitalReportPage() {
  const profile = await requireRole("patient");

  return (
    <AppShell
      role="patient"
      title="Nueva medición"
      subtitle="Registra tus signos vitales; Carmen evaluará el riesgo."
    >
      <div className="max-w-3xl">
        <VitalReportForm patientId={profile.id} />
      </div>
    </AppShell>
  );
}
