import Link from "next/link";
import { Activity, ShieldCheck } from "lucide-react";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#f7faf9] px-6 py-10 text-ink">
      <section className="mx-auto flex max-w-5xl flex-col gap-8">
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-md bg-clinical text-white">
            <Activity aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-3xl font-semibold tracking-normal">HomecareCCV</h1>
            <p className="text-sm text-slate-600">Universidad Nacional de Colombia</p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Link className="rounded-md border border-slate-200 bg-white p-5 shadow-sm" href="/login">
            <ShieldCheck className="mb-4 text-clinical" aria-hidden="true" />
            <h2 className="text-lg font-semibold">Ingreso clínico</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Acceso protegido para pacientes, IPS y administración.
            </p>
          </Link>
          <Link className="rounded-md border border-slate-200 bg-white p-5 shadow-sm" href="/patient/dashboard">
            <h2 className="text-lg font-semibold">Paciente</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">Riesgo actual, historial y recomendaciones.</p>
          </Link>
          <Link className="rounded-md border border-slate-200 bg-white p-5 shadow-sm" href="/ips/alerts">
            <h2 className="text-lg font-semibold">IPS</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">Alertas priorizadas y seguimiento poblacional.</p>
          </Link>
        </div>
      </section>
    </main>
  );
}
