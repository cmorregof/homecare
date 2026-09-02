import Image from "next/image";
import { Heart } from "lucide-react";

import { BRAND_NAME, BRAND_TAGLINE } from "@/lib/brand";
import { cn } from "@/lib/utils";

/**
 * Split auth layout, ported from the reference `.auth-shell` / `.auth-card`
 * (proyecto_daniela @ 1aa2b0a — global.css:65-118): two equal columns with a
 * hero on the left and a bordered card on the right, collapsing to one column
 * at 900px. `wide` is the reference's `.auth-card.wide`.
 *
 * The reference's hero is a flat #D32F2F -> #9A0007 gradient. Ours keeps that
 * structure and adds the project's own cover illustration — the Andean
 * household CARMEN is named for — as a band along the bottom.
 *
 * A band rather than a background: the artwork is a 4:1 panorama and this
 * column is portrait, so covering it would crop away 82% of the image,
 * including the grandmother taking the blood pressure the whole product is
 * about. At its own ratio it stays legible and Next serves a source that
 * matches, instead of upscaling a 750px file across a 1000px height.
 */
export function AuthShell({ wide = false, children }: { wide?: boolean; children: React.ReactNode }) {
  return (
    <main className="grid min-h-screen grid-cols-1 bg-canvas lg:grid-cols-2">
      <div className="relative flex flex-col justify-end overflow-hidden bg-gradient-to-br from-brand to-brand-dark text-white">
        <div className="relative z-10 flex flex-1 flex-col justify-center px-8 py-12 lg:px-14 lg:py-16">
          <Heart className="mb-5 h-14 w-14 fill-current" aria-hidden />
          <h2 className="text-5xl font-extrabold leading-[1.05]">{BRAND_NAME}</h2>
          <p className="mt-2 text-xl font-semibold text-white/95">{BRAND_TAGLINE}</p>
          <p className="mt-4 max-w-[460px] text-lg leading-relaxed text-white/90">
            Monitoreo cardiovascular domiciliario con seguimiento clínico continuo y alertas en tiempo real.
          </p>
        </div>
        <div className="relative aspect-[4/1] w-full shrink-0">
          <Image
            src="/carmen-portada.jpg"
            alt="Una familia campesina en los Andes colombianos; la abuela toma la presión arterial al abuelo en el corredor de la casa."
            fill
            priority
            sizes="(max-width: 1024px) 100vw, 50vw"
            className="object-cover"
          />
          {/* Fades the panorama into the gradient instead of butting against it. */}
          <div
            aria-hidden
            className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-brand-dark to-transparent"
          />
        </div>
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
