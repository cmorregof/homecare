import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";

import { supabaseAnonKey, supabaseUrl } from "@/lib/supabase";

export function createServerSupabaseClient() {
  const cookieStore = cookies();
  type CookieOptions = Parameters<typeof cookieStore.set>[2];
  type CookieToSet = { name: string; value: string; options?: CookieOptions };

  return createServerClient(
    supabaseUrl || "https://example.supabase.co",
    supabaseAnonKey || "public-anon-key",
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet: CookieToSet[]) {
          try {
            cookiesToSet.forEach(({ name, value, options }) => {
              cookieStore.set(name, value, options);
            });
          } catch {
            // Server components cannot always write cookies; middleware refreshes sessions.
          }
        },
      },
    },
  );
}
