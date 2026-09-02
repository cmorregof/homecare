import { ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Timezone every clinical timestamp is formatted in.
 *
 * Without it, `Intl.DateTimeFormat` uses the runtime's zone: UTC on the server,
 * the viewer's own zone in the browser. That had two consequences. Server-
 * rendered pages showed Colombian readings five hours late — an alert raised at
 * 05:56 displayed as 10:56. And `AlertRow`, which is server-rendered inside
 * /ips/dashboard but client-rendered inside RealtimeAlertList, produced two
 * different strings for the same alert and broke hydration (React #425).
 *
 * Pinned rather than left to the viewer because these are clinical records of
 * when a measurement was taken in Colombia, not appointments in the reader's
 * own day. Colombia does not observe DST, so the offset is a constant -05:00.
 */
const CLINICAL_TIME_ZONE = "America/Bogota";

/**
 * Formats a clinical timestamp. Use this rather than `Intl.DateTimeFormat`
 * directly: it fixes both ways the raw API goes wrong here.
 *
 * The zone, per the note above. And the spaces: Node's ICU renders the es-CO
 * day period as `a.<U+0020>m.` while Chrome's renders `a.<U+00A0>m.` — the same
 * glyph, a different codepoint. React compares text by codepoint, so a row
 * rendered on the server and hydrated in the browser mismatched on a character
 * nobody can see. That is the real cause of the hydration error on /ips/alerts
 * (React #425); the timezone was a separate bug found alongside it.
 */
export function formatClinical(value: string | Date, options: Intl.DateTimeFormatOptions) {
  return new Intl.DateTimeFormat("es-CO", { timeZone: CLINICAL_TIME_ZONE, ...options })
    .format(new Date(value))
    .replace(/[\u00a0\u202f]/g, " ");
}
