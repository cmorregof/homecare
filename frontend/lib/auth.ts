import { redirect } from "next/navigation";

import { getCurrentProfile } from "@/lib/data";
import type { UserRole } from "@/types";

const ROLE_HOME: Record<UserRole, string> = {
  patient: "/patient/dashboard",
  ips: "/ips/dashboard",
  admin: "/admin/dashboard",
};

export function homeForRole(role: UserRole) {
  return ROLE_HOME[role];
}

export async function requireRole(role: UserRole) {
  const profile = await getCurrentProfile(role);
  if (!profile) {
    redirect("/login");
  }
  if (profile.role !== role) {
    redirect(homeForRole(profile.role));
  }
  return profile;
}
