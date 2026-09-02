import { Heart } from "lucide-react";

import { BRAND_NAME, BRAND_TAGLINE } from "@/lib/brand";

import { cn } from "@/lib/utils";

/**
 * Split auth layout, ported from the reference `.auth-shell` / `.auth-card`
 * (proyecto_daniela @ 1aa2b0a — global.css:65-118): two equal columns with a
 * gradient hero on the left and a bordered card on the right, collapsing to
 * one column at 900px. `wide` is the reference's `.auth-card.wide`.
 *
 * The reference's hero gradient runs #D32F2F → #9A0007. Here it runs through
 * the brand blues instead: that red is now the critical-risk fill, and a
 * login screen is not an emergency.
 */
export function AuthShell({ wide = false, children }: { wide?: boolean; children: React.ReactNode }) {
  return (
    <main className="grid min-h-screen grid-cols-1 bg-canvas lg:grid-cols-2">
      <div className="flex flex-col justify-center bg-gradient-to-br from-brand to-brand-dark px-8 py-12 text-white lg:px-14 lg:py-16">
        <Heart className="mb-6 h-16 w-16 fill-current" aria-hidden />
        <h2 className="text-5xl font-extrabold leading-[1.05]">{BRAND_NAME}</h2>
        <p className="mt-2 text-xl font-semibold text-white/90">{BRAND_TAGLINE}</p>
        <p className="mt-4 max-w-[460px] text-lg leading-relaxed text-white/80">
          Monitoreo cardiovascular domiciliario con seguimiento clínico continuo y alertas en tiempo real.
        </p>
      </div>
      <div className="flex items-center justify-center px-6 py-12 lg:px-16">
        <section
          className={cn(
            "w-full rounded-lg border border-border bg-surface p-8 shadow-md",
            wide ? "max-w-[720px]" : "max-w-[420px]",
          )}
        >
          {children}
        </section>
      </div>
    </main>
  );
}
