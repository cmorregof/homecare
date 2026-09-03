import { NextRequest, NextResponse } from "next/server";

import { createServerSupabaseClient } from "@/lib/supabase-server";
import { BRAND_NAME } from "@/lib/brand";
import { ROLE_HOME, toPublicRole } from "@/lib/roles";
import type { UserRole } from "@/types";

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
  const fullName = String(metadata.full_name || user.email || `Usuario ${BRAND_NAME}`);
  const documentId = metadata.document_id ? String(metadata.document_id) : null;

  // Does the profile already exist? Two different writes follow from the answer,
  // and conflating them is what made this route dangerous.
  const { data: existing } = await supabase
    .from("profiles")
    .select("role")
    .eq("id", user.id)
    .maybeSingle();
  const existingRole = (existing as { role: UserRole } | null)?.role;

  if (existingRole) {
    // Confirming an email must never restate the role. The previous upsert did,
    // which meant an administrator created from /admin/users was demoted back to
    // whatever `user_metadata.role` said the moment they followed a confirmation
    // link. Since the role lock landed, that write is refused outright and the
    // user is bounced to the login screen with a database error instead.
    const { error: updateError } = await supabase
      .from("profiles")
      .update({ full_name: fullName, document_id: documentId })
      .eq("id", user.id);
    if (updateError) {
      return redirectToLogin(requestUrl, updateError.message);
    }
    return NextResponse.redirect(new URL(ROLE_HOME[existingRole], requestUrl.origin));
  }

  // First confirmation. `user_metadata` is written by whoever called signUp(),
  // so the role in it is the caller's claim, not a fact: 'admin' there was
  // enough to become one. toPublicRole refuses anything outside patient/ips.
  const role = toPublicRole(metadata.role);
  const { error: profileError } = await supabase
    .from("profiles")
    .insert({ id: user.id, full_name: fullName, document_id: documentId, role });
  if (profileError) {
    return redirectToLogin(requestUrl, profileError.message);
  }

  return NextResponse.redirect(new URL(ROLE_HOME[role], requestUrl.origin));
}

function redirectToLogin(requestUrl: URL, message: string) {
  const loginUrl = new URL("/login", requestUrl.origin);
  loginUrl.searchParams.set("message", message);
  return NextResponse.redirect(loginUrl);
}
