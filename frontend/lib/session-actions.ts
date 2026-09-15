"use server";

import { redirect } from "next/navigation";

import { isSupabaseConfigured } from "@/lib/supabase";
import { createServerSupabaseClient } from "@/lib/supabase-server";

/**
 * Ends the session and returns to the login screen.
 *
 * The control this replaces was `<Link href="/login">`. It navigated to the
 * login page without touching the session: the auth cookie stayed valid, so
 * pressing Back — or opening /patient/dashboard again — returned the previous
 * user to their account. `/login` is not in the middleware matcher
 * (middleware.ts:84), so it rendered normally and looked like a successful
 * logout. On a phone shared with family that is a privacy failure, not a
 * cosmetic one.
 *
 * It runs on the server so the cookie is cleared by the response itself. A
 * browser-side signOut() would depend on the page staying alive long enough to
 * write the cookie back, and this one navigates away immediately.
 */
export async function signOutAction() {
  if (isSupabaseConfigured()) {
    const supabase = createServerSupabaseClient();
    const { error } = await supabase.auth.signOut();
    if (error) {
      console.error(`[homecare] No se pudo cerrar la sesión: ${error.message}`);
      redirect("/login?message=No%20se%20pudo%20cerrar%20la%20sesi%C3%B3n.%20Intenta%20de%20nuevo.");
    }
  }
  redirect("/login?message=Sesi%C3%B3n%20cerrada.");
}
