import { createBrowserClient } from "@supabase/ssr";

export const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
export const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

export function isSupabaseConfigured() {
  return Boolean(supabaseUrl && supabaseAnonKey && supabaseUrl.includes(".supabase.co"));
}

export function createBrowserSupabaseClient() {
  return createBrowserClient(
    supabaseUrl || "https://example.supabase.co",
    supabaseAnonKey || "public-anon-key",
  );
}

export const supabase = createBrowserSupabaseClient();
