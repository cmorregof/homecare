import { NextRequest, NextResponse } from "next/server";

import { createServerSupabaseClient } from "@/lib/supabase-server";
import type { UserRole } from "@/types";

const ROLE_HOME: Record<UserRole, string> = {
  patient: "/patient/dashboard",
  ips: "/ips/dashboard",
  admin: "/admin/dashboard",
};

const VALID_ROLES = new Set<UserRole>(["patient", "ips", "admin"]);

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const error = requestUrl.searchParams.get("error");
  const errorDescription = requestUrl.searchParams.get("error_description");

  if (error) {
    return redirectToLogin(requestUrl, errorDescription || error);
  }

  if (!code) {
    return redirectToLogin(requestUrl, "No se encontró el código de confirmación.");
  }

  const supabase = createServerSupabaseClient();
  const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
  if (exchangeError) {
    return redirectToLogin(requestUrl, exchangeError.message);
  }

  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError || !user) {
    return redirectToLogin(requestUrl, userError?.message || "No se pudo confirmar la sesión.");
  }

  const metadata = user.user_metadata ?? {};
  const role = normalizeRole(metadata.role);
  const profilePayload = {
    id: user.id,
    full_name: String(metadata.full_name || user.email || "Usuario HomecareCCV"),
    document_id: metadata.document_id ? String(metadata.document_id) : null,
    role,
  };

  const { error: profileError } = await supabase.from("profiles").upsert(profilePayload, { onConflict: "id" });
  if (profileError) {
    return redirectToLogin(requestUrl, profileError.message);
  }

  return NextResponse.redirect(new URL(ROLE_HOME[role], requestUrl.origin));
}

function normalizeRole(value: unknown): UserRole {
  if (typeof value === "string" && VALID_ROLES.has(value as UserRole)) {
    return value as UserRole;
  }
  return "patient";
}

function redirectToLogin(requestUrl: URL, message: string) {
  const loginUrl = new URL("/login", requestUrl.origin);
  loginUrl.searchParams.set("message", message);
  return NextResponse.redirect(loginUrl);
}
