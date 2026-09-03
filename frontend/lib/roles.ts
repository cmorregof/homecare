import type { UserRole } from "@/types";

/**
 * Roles a person may give themselves when signing up.
 *
 * 'admin' is absent, and that absence is enforced in three places because any
 * one of them alone is bypassable:
 *
 *   1. Here and in the register form, which no longer offers the option.
 *   2. In app/auth/callback/route.ts, which used to copy `user_metadata.role`
 *      straight into the profile. That field is supplied by the client at
 *      signUp() and is therefore attacker-controlled: removing the dropdown
 *      entry alone left the door open to anyone willing to post the request
 *      themselves.
 *   3. In the database, by profiles_insert_own
 *      (backend/db/migrations/20260903_lock_profile_role.sql), which is the
 *      only one of the three that a determined caller cannot route around.
 *
 * An administrator is created by an existing administrator, from
 * /admin/users.
 */
export const PUBLIC_ROLES = ["patient", "ips"] as const;

export type PublicRole = (typeof PUBLIC_ROLES)[number];

export function isPublicRole(value: unknown): value is PublicRole {
  return typeof value === "string" && (PUBLIC_ROLES as readonly string[]).includes(value);
}

/**
 * Clamps any client-supplied role to one the public is allowed to hold.
 * Anything unrecognised — or 'admin' — becomes 'patient'.
 */
export function toPublicRole(value: unknown): PublicRole {
  return isPublicRole(value) ? value : "patient";
}

export const ROLE_HOME: Record<UserRole, string> = {
  patient: "/patient/dashboard",
  ips: "/ips/dashboard",
  admin: "/admin/dashboard",
};
