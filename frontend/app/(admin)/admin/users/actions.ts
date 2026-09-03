"use server";

import { revalidatePath } from "next/cache";

import { isSupabaseConfigured } from "@/lib/supabase";
import { createServerSupabaseClient } from "@/lib/supabase-server";
import type { UserRole } from "@/types";

/**
 * Writes from the admin user screen.
 *
 * Before these existed, `UserManagement` changed a role or a doctor in React
 * state and nothing else (components/admin/user-management.tsx:35). With mock
 * names that read as an obvious demo; with the real directory it looks like a
 * saved change that silently disappears on reload.
 *
 * They run under the administrator's own session, not a service key, so the
 * database is the one granting the permission: profiles_update_admin decides
 * whether the write lands. The role check below is for a legible error message,
 * not for security — a caller who skips it still hits RLS.
 */

export type ActionResult = { ok: true } | { ok: false; error: string };

const ROLES: UserRole[] = ["patient", "ips", "admin"];

export async function updateUserRole(userId: string, role: UserRole): Promise<ActionResult> {
  if (!ROLES.includes(role)) {
    return { ok: false, error: "Rol no válido." };
  }
  const context = await adminContext();
  if (!context.ok) {
    return context;
  }
  // Changing your own role from this screen is refused: an administrator who
  // demotes themselves loses the screen and cannot undo it, and RLS does allow
  // the write (profiles_update_admin passes because the role is still 'admin'
  // while the statement is being checked). Recovery would need the service key.
  if (userId === context.adminId) {
    return { ok: false, error: "No puedes cambiar tu propio rol desde aquí." };
  }

  const { error } = await context.supabase.from("profiles").update({ role }).eq("id", userId);
  if (error) {
    console.error(`[homecare] No se pudo cambiar el rol de ${userId}: ${error.message}`);
    return { ok: false, error: "No se pudo guardar el rol." };
  }
  revalidatePath("/admin/users");
  return { ok: true };
}

export async function assignDoctor(patientId: string, doctorId: string | null): Promise<ActionResult> {
  const context = await adminContext();
  if (!context.ok) {
    return context;
  }

  if (doctorId) {
    // Only an IPS profile can be a treating doctor. Without this check the
    // column would happily point at a patient: assigned_doctor_id references
    // profiles(id) with no role constraint (backend/db/schemas.sql:64).
    const { data: doctor, error } = await context.supabase
      .from("profiles")
      .select("role")
      .eq("id", doctorId)
      .single();
    if (error || !doctor) {
      return { ok: false, error: "No se encontró el profesional seleccionado." };
    }
    if ((doctor as { role: UserRole }).role !== "ips") {
      return { ok: false, error: "Solo un perfil IPS puede quedar como médico asignado." };
    }
  }

  const { error } = await context.supabase
    .from("profiles")
    .update({ assigned_doctor_id: doctorId })
    .eq("id", patientId);
  if (error) {
    console.error(`[homecare] No se pudo asignar el médico de ${patientId}: ${error.message}`);
    return { ok: false, error: "No se pudo guardar la asignación." };
  }
  revalidatePath("/admin/users");
  return { ok: true };
}

type AdminContext =
  | { ok: true; supabase: ReturnType<typeof createServerSupabaseClient>; adminId: string }
  | { ok: false; error: string };

async function adminContext(): Promise<AdminContext> {
  if (!isSupabaseConfigured()) {
    return { ok: false, error: "Supabase no está configurado: la pantalla muestra datos de demostración." };
  }
  const supabase = createServerSupabaseClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return { ok: false, error: "La sesión expiró. Vuelve a entrar." };
  }
  const { data: profile } = await supabase.from("profiles").select("role").eq("id", user.id).single();
  if ((profile as { role: UserRole } | null)?.role !== "admin") {
    return { ok: false, error: "Solo un administrador puede cambiar usuarios." };
  }
  return { ok: true, supabase, adminId: user.id };
}
