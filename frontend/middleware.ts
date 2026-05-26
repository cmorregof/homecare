import { type NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";

import { supabaseAnonKey, supabaseUrl } from "@/lib/supabase";
import type { UserRole } from "@/types";

const ROLE_PATHS: Record<UserRole, string> = {
  patient: "/patient",
  ips: "/ips",
  admin: "/admin",
};

const ROLE_HOME: Record<UserRole, string> = {
  patient: "/patient/dashboard",
  ips: "/ips/dashboard",
  admin: "/admin/dashboard",
};

export async function middleware(request: NextRequest) {
  if (!supabaseUrl || !supabaseAnonKey || !supabaseUrl.includes(".supabase.co")) {
    return NextResponse.next();
  }

  let response = NextResponse.next({ request });
  type CookieOptions = Parameters<typeof response.cookies.set>[2];
  type CookieToSet = { name: string; value: string; options?: CookieOptions };
  const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet: CookieToSet[]) {
        cookiesToSet.forEach(({ name, value, options }) => {
          request.cookies.set(name, value);
          response = NextResponse.next({ request });
          response.cookies.set(name, value, options);
        });
      },
    },
  });

  const {
    data: { user },
  } = await supabase.auth.getUser();
  const pathname = request.nextUrl.pathname;
  const requiredRole = roleForPath(pathname);

  if (!requiredRole) {
    return response;
  }

  if (!user) {
    return NextResponse.redirect(new URL(`/login?next=${encodeURIComponent(pathname)}`, request.url));
  }

  const { data: profile } = await supabase.from("profiles").select("role").eq("id", user.id).single();
  const role = profile?.role as UserRole | undefined;

  if (!role) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (role !== requiredRole) {
    return NextResponse.redirect(new URL(ROLE_HOME[role], request.url));
  }

  return response;
}

function roleForPath(pathname: string): UserRole | null {
  if (pathname.startsWith(ROLE_PATHS.patient)) {
    return "patient";
  }
  if (pathname.startsWith(ROLE_PATHS.ips)) {
    return "ips";
  }
  if (pathname.startsWith(ROLE_PATHS.admin)) {
    return "admin";
  }
  return null;
}

export const config = {
  matcher: ["/patient/:path*", "/ips/:path*", "/admin/:path*"],
};
