import { randomBytes } from "node:crypto";

import { NextRequest, NextResponse } from "next/server";

import { sendCredentialsEmail } from "@/lib/credentials-email";
import { isPublicRole } from "@/lib/roles";
import { getSiteUrl } from "@/lib/site-url";
import { createServerSupabaseClient } from "@/lib/supabase-server";
import { createServiceSupabaseClient } from "@/lib/supabase-service";
import type { UserRole } from "@/types";

/**
 * Creates a user on behalf of an administrator.
 *
 * This is the only path that can produce an administrator, and it exists
 * because the public one no longer can. Creating an account means creating an
 * `auth.users` row, which needs the service role key, which bypasses RLS —
 * so authorisation is entirely this handler's responsibility and is done
 * before the key is ever touched:
 *
 *   1. the caller's own cookie session identifies them, and
 *   2. their `profiles.role` is read with their own credentials, under RLS.
 *
 * It lives here rather than in FastAPI because the backend has no
 * authentication of any kind and allow_origins=["*"] (backend/main.py:24). A
 * service-key endpoint there would let anyone on the internet mint
 * administrators — a wider hole than the one this branch closes.
 *
 * Node runtime, not Edge: randomBytes and the service client need it.
 */
export const runtime = "nodejs";

const VALID_ROLES: UserRole[] = ["patient", "ips", "admin"];

export async function POST(request: NextRequest) {
  const supabase = createServerSupabaseClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Sesión no válida." }, { status: 401 });
  }

  const { data: caller } = await supabase.from("profiles").select("role").eq("id", user.id).single();
  if ((caller as { role: UserRole } | null)?.role !== "admin") {
    return NextResponse.json({ error: "Solo un administrador puede crear usuarios." }, { status: 403 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Cuerpo de la petición no válido." }, { status: 400 });
  }

  const { email, fullName, documentId, role } = normalize(body);
  if (!email || !fullName) {
    return NextResponse.json({ error: "El correo y el nombre son obligatorios." }, { status: 400 });
  }
  if (!VALID_ROLES.includes(role)) {
    return NextResponse.json({ error: "Rol no válido." }, { status: 400 });
  }

  const service = createServiceSupabaseClient();
  if (!service) {
    return NextResponse.json(
      {
        error:
          "Falta SUPABASE_SERVICE_KEY en el servidor. Sin esa clave no se pueden crear cuentas.",
      },
      { status: 503 },
    );
  }

  const password = generatePassword();
  const { data: created, error: createError } = await service.auth.admin.createUser({
    email,
    password,
    // Confirmed on creation: the account was made by an administrator, and the
    // credentials email doubles as the notification. Leaving it unconfirmed
    // would send the user through a link that then reasserts a role from
    // metadata (app/auth/callback/route.ts).
    email_confirm: true,
    user_metadata: { full_name: fullName, document_id: documentId },
  });
  if (createError || !created?.user) {
    const message = createError?.message ?? "No se pudo crear la cuenta.";
    // Supabase reports an existing address as a 422; say so in plain language.
    const conflict = /already|registered|exists/i.test(message);
    return NextResponse.json(
      { error: conflict ? "Ya existe una cuenta con ese correo." : message },
      { status: conflict ? 409 : 502 },
    );
  }

  // The role is written with the service key, which is what allows 'admin'
  // here and nowhere else. isPublicRole marks the distinction explicitly.
  const { error: profileError } = await service.from("profiles").insert({
    id: created.user.id,
    full_name: fullName,
    document_id: documentId,
    role,
  });
  if (profileError) {
    // Roll the auth user back: an account with no profile cannot log in
    // anywhere useful, and it would block the address from being reused.
    await service.auth.admin.deleteUser(created.user.id);
    return NextResponse.json(
      { error: `La cuenta no se creó: ${profileError.message}` },
      { status: 502 },
    );
  }

  const delivery = await sendCredentialsEmail({
    to: email,
    fullName,
    password,
    loginUrl: `${getSiteUrl()}/login`,
  });

  return NextResponse.json({
    profile: {
      id: created.user.id,
      full_name: fullName,
      document_id: documentId,
      role,
      email,
    },
    emailSent: delivery.sent,
    emailError: delivery.reason,
    // Returned so the administrator can pass the password on when the email did
    // not go out. It is never stored: Supabase keeps only a bcrypt hash, so this
    // response is the last point at which the value exists in readable form.
    password: delivery.sent ? undefined : password,
    privileged: !isPublicRole(role),
  });
}

function normalize(body: unknown) {
  const raw = (body ?? {}) as Record<string, unknown>;
  return {
    email: String(raw.email ?? "").trim().toLowerCase(),
    fullName: String(raw.fullName ?? "").trim(),
    documentId: raw.documentId ? String(raw.documentId).trim() : null,
    role: String(raw.role ?? "patient") as UserRole,
  };
}

/**
 * A 20-character password from a 57-symbol alphabet: about 117 bits of entropy,
 * generated with the CSPRNG rather than Math.random.
 *
 * The alphabet omits I, l, O, o, 0 and 1, because this password gets read off a
 * screen and typed by hand at least once. Bytes are drawn through a rejection
 * loop: 256 is not a multiple of 57, so a plain modulo would favour the first
 * few letters.
 */
function generatePassword(length = 20) {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789";
  const limit = 256 - (256 % alphabet.length);
  let out = "";
  while (out.length < length) {
    for (const byte of randomBytes(length)) {
      if (byte < limit) {
        out += alphabet[byte % alphabet.length];
        if (out.length === length) {
          break;
        }
      }
    }
  }
  return out;
}
