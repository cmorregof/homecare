"use client";

import { useState, useTransition } from "react";

import { assignDoctor, updateUserRole } from "@/app/(admin)/admin/users/actions";
import { Alert } from "@/components/alerts/alert-row";
import { EmptyState } from "@/components/ui/empty-state";
import { Table, TableWrap, Td, Th, Tr } from "@/components/ui/table";
import type { Profile, UserRole } from "@/types";

/**
 * The user directory, backed by `profiles`.
 *
 * Both selects write through server actions and then re-read the row from the
 * response. They used to change React state only, so a role or a doctor picked
 * here vanished on the next reload; with the real directory in place that would
 * have been indistinguishable from a saved change.
 *
 * The "create user" form that stood here has been removed rather than left
 * disabled: it pushed an object with `id: draft-<timestamp>` into local state
 * and never reached the database. Creating a user means creating an auth
 * account, which needs the service key and a server route that does not exist
 * yet.
 */
export function UserManagement({ initialProfiles }: { initialProfiles: Profile[] }) {
  const [profiles, setProfiles] = useState(initialProfiles);
  const [error, setError] = useState("");
  const [pending, startTransition] = useTransition();

  const doctors = profiles.filter((profile) => profile.role === "ips");

  function applyRole(id: string, nextRole: UserRole) {
    const previous = profiles;
    setError("");
    setProfiles((current) =>
      current.map((profile) => (profile.id === id ? { ...profile, role: nextRole } : profile)),
    );
    startTransition(async () => {
      const result = await updateUserRole(id, nextRole);
      if (!result.ok) {
        setProfiles(previous);
        setError(result.error);
      }
    });
  }

  function applyDoctor(id: string, doctorId: string) {
    const previous = profiles;
    const next = doctorId || null;
    setError("");
    setProfiles((current) =>
      current.map((profile) => (profile.id === id ? { ...profile, assigned_doctor_id: next } : profile)),
    );
    startTransition(async () => {
      const result = await assignDoctor(id, next);
      if (!result.ok) {
        setProfiles(previous);
        setError(result.error);
      }
    });
  }

  return (
    <div className="grid gap-4">
      {error ? <Alert tone="error">{error}</Alert> : null}

      <TableWrap>
        {profiles.length === 0 ? (
          <EmptyState>No hay usuarios registrados.</EmptyState>
        ) : (
          <div className="min-w-[680px]">
            <Table>
              <thead>
                <tr>
                  <Th>Usuario</Th>
                  <Th>Rol</Th>
                  <Th>Médico asignado</Th>
                </tr>
              </thead>
              <tbody>
                {profiles.map((profile) => (
                  <Tr key={profile.id}>
                    <Td>
                      <p className="font-semibold text-ink">{profile.full_name}</p>
                      <p className="text-xs text-muted">{profile.document_id ?? profile.email ?? profile.id}</p>
                    </Td>
                    <Td>
                      <label htmlFor={`role-${profile.id}`} className="sr-only">
                        Rol de {profile.full_name}
                      </label>
                      <select
                        id={`role-${profile.id}`}
                        value={profile.role}
                        disabled={pending}
                        onChange={(event) => applyRole(profile.id, event.target.value as UserRole)}
                        className={INLINE_SELECT}
                      >
                        <option value="patient">Paciente</option>
                        <option value="ips">IPS</option>
                        <option value="admin">Admin</option>
                      </select>
                    </Td>
                    <Td>
                      <label htmlFor={`doctor-${profile.id}`} className="sr-only">
                        Médico asignado a {profile.full_name}
                      </label>
                      <select
                        id={`doctor-${profile.id}`}
                        value={profile.assigned_doctor_id ?? ""}
                        disabled={pending || profile.role !== "patient"}
                        onChange={(event) => applyDoctor(profile.id, event.target.value)}
                        className={INLINE_SELECT}
                      >
                        <option value="">Sin asignar</option>
                        {doctors.map((doctor) => (
                          <option key={doctor.id} value={doctor.id}>
                            {doctor.full_name}
                          </option>
                        ))}
                      </select>
                    </Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          </div>
        )}
      </TableWrap>
    </div>
  );
}

/** Compact control for use inside a table cell. */
const INLINE_SELECT =
  "rounded-md border border-border bg-surface px-2 py-1.5 text-base text-ink outline-none transition focus:border-brand focus:ring-[3px] focus:ring-brand/[0.12] disabled:cursor-not-allowed disabled:opacity-60";
