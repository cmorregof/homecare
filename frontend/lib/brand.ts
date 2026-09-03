/**
 * Product identity, in one place so the nine copies that used to be scattered
 * across the UI cannot drift apart.
 *
 * NOTE ON THE COLLISION: the product and the nurse agent are both called
 * Carmen. That is deliberate — the product is named after the agent — but it
 * means chat surfaces should say "Carmen" (the persona speaking) and never
 * "CARMEN" (the product), or the greeting reads as the software introducing
 * itself instead of the nurse.
 */
export const BRAND_NAME = "CARMEN";

/** Descriptor shown under or beside the name. Never used alone as a title. */
export const BRAND_TAGLINE = "Salud cardiaca";

/** For the browser tab and anywhere the two must appear as one string. */
export const BRAND_FULL = `${BRAND_NAME} · ${BRAND_TAGLINE}`;

/**
 * Telegram channel, where CARMEN already works. Used as the fallback route the
 * web form points to when it cannot reach the backend, and by the patient
 * dashboard button — one literal so the two cannot drift apart.
 */
export const TELEGRAM_BOT_URL =
  process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ?? "https://t.me/project918_homecare_bot";
