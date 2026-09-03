import { createClient } from "@supabase/supabase-js";

import { supabaseUrl } from "@/lib/supabase";

/**
 * Supabase client holding the service role key.
 *
 * The service role bypasses every RLS policy, including the ones that stop a
 * user making themselves an administrator, so this module must never reach the
 * browser. Two things keep it there: the variable has no NEXT_PUBLIC_ prefix,
 * so Next.js never inlines it into the client bundle and the key would read as
 * undefined there anyway; and the throw below turns a mistaken client import
 * into an immediate, obvious failure instead of a silently broken call.
 *
 * (`server-only`, the usual guard, is not a dependency of this project and
 * adding one is out of scope here.)
 *
 * Every caller must establish for itself that the request comes from an
 * administrator. This client will not do it for them — that is the point of
 * the key.
 */
export function createServiceSupabaseClient() {
  if (typeof window !== "undefined") {
    throw new Error("createServiceSupabaseClient() no puede usarse en el navegador.");
  }
  const serviceKey = process.env.SUPABASE_SERVICE_KEY;
  if (!supabaseUrl || !serviceKey) {
    return null;
  }
  return createClient(supabaseUrl, serviceKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
}

export function isServiceRoleConfigured() {
  return Boolean(supabaseUrl && process.env.SUPABASE_SERVICE_KEY);
}
