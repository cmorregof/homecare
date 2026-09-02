import { FlaskConical } from "lucide-react";

import { demoNoticeFor } from "@/lib/demo-mode";
import type { UserRole } from "@/types";

/**
 * Persistent notice that the screen is showing invented data.
 *
 * It deliberately does NOT use the danger or warning tokens. Those hues mean
 * "this patient is at risk"; this bar means "none of this is a patient". Using
 * red here would put a system-configuration problem and a clinical emergency in
 * the same visual language. It is dark chrome with a mono label instead —
 * unmistakable, and unlike every risk tier.
 */
export function DemoBanner({ role }: { role: UserRole }) {
  const notice = demoNoticeFor(role);
  if (!notice) {
    return null;
  }

  return (
    <div role="status" className="flex items-start gap-3 bg-ink px-4 py-2.5 text-white lg:px-10">
      <FlaskConical className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <p className="text-sm leading-relaxed">
        <span className="mr-2 font-mono text-[11px] font-semibold uppercase tracking-[0.08em] text-brand-light">
          Datos de demostración
        </span>
        {notice.level === "all" ? (
          <>
            Supabase no está configurado. <strong className="font-semibold">Nada</strong> de lo que ves en esta
            pantalla proviene de la base de datos: son datos inventados de <code>mock-data.ts</code>. No tomes
            decisiones clínicas con esta información.
          </>
        ) : (
          <>
            Supabase está configurado, pero {listado(notice.datasets)}{" "}
            {notice.datasets.length === 1 ? "sigue viniendo" : "siguen viniendo"} de{" "}
            <code>mock-data.ts</code>, no de la base de datos. Son datos inventados.
          </>
        )}
      </p>
    </div>
  );
}

function listado(items: string[]) {
  if (items.length <= 1) {
    return items[0] ?? "";
  }
  return `${items.slice(0, -1).join(", ")} y ${items[items.length - 1]}`;
}
