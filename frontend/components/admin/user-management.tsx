"use client";

import { FormEvent, useState, useTransition } from "react";
import { UserPlus } from "lucide-react";

import { assignDoctor, updateUserRole } from "@/app/(admin)/admin/users/actions";
import { Alert } from "@/components/alerts/alert-row";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Field, SelectField } from "@/components/ui/field";
import { Table, TableWrap, Td, Th, Tr } from "@/components/ui/table";
import { Card, CardTitle } from "@/components/vitals/vital-card";
import type { Profile, UserRole } from "@/types";

/**
 * The user directory, backed by `profiles`.
 *
 * Both selects write through server actions and then re-read the row from the
 * response. They used to change React state only, so a role or a doctor picked
 * here vanished on the next reload; with the real directory in place that would
 * have been indistinguishable from a saved change.
 *
 * The create form posts to /api/admin/users, which holds the service key. It
 * used to push an object with `id: draft-<timestamp>` into local state and
 * never reach the database, so every user it "created" disappeared on reload.
 *
 * This is the only screen in the product that can produce an administrator;
 * the public signup path cannot, by policy and by RLS.
 */
type Created = { fullName: string; email: string; password?: string; emailError?: string };

export function UserManagement({ initialProfiles }: { initialProfiles: Profile[] }) {
  const [profiles, setProfiles] = useState(initialProfiles);
  const [error, setError] = useState("");
  const [pending, startTransition] = useTransition();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [newRole, setNewRole] = useState<UserRole>("patient");
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<Created | null>(null);

  const doctors = profiles.filter((profile) => profile.role === "ips");

  async function createUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setCreated(null);
    if (!name.trim() || !email.trim()) {
      setError("El nombre y el correo son obligatorios.");
      return;
    }
    setCreating(true);
    try {
      const response = await fetch("/api/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fullName: name.trim(),
          email: email.trim(),
          documentId: documentId.trim() || null,
          role: newRole,
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        setError(payload.error ?? "No se pudo crear la cuenta.");
        return;
      }
      setProfiles((current) => [...current, payload.profile as Profile]);
      setCreated({
        fullName: name.trim(),
        email: email.trim(),
        password: payload.password,
        emailError: payload.emailError,
      });
      setName("");
      setEmail("");
      setDocumentId("");
      setNewRole("patient");
    } catch {
      setError("No se pudo contactar al servidor.");
    } finally {
      setCreating(false);
    }
  }

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
    <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
      <div className="space-y-4">
        <Card>
          <form onSubmit={createUser}>
            <CardTitle>Crear usuario</CardTitle>
            <Field label="Nombre completo" value={name} onChange={(event) => setName(event.target.value)} />
            <Field
              label="Correo"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              helper="Recibirá ahí su contraseña temporal."
            />
            <Field
              label="Documento (opcional)"
              value={documentId}
              onChange={(event) => setDocumentId(event.target.value)}
            />
            <SelectField
              label="Rol"
              value={newRole}
              onChange={(event) => setNewRole(event.target.value as UserRole)}
              helper="Esta pantalla es el único sitio desde donde se crea un administrador."
            >
              <option value="patient">Paciente</option>
              <option value="ips">IPS</option>
              <option value="admin">Admin</option>
            </SelectField>
            <Button type="submit" full className="mt-2" disabled={creating}>
              <UserPlus className="h-4 w-4" aria-hidden />
              {creating ? "Creando…" : "Crear"}
            </Button>
          </form>
        </Card>

        {error ? <Alert tone="error">{error}</Alert> : null}
        {created ? <CredentialsNotice created={created} /> : null}
      </div>

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

/**
 * Shown once, right after a user is created.
 *
 * The password appears here only when the email did not go out. Supabase keeps
 * a bcrypt hash and nothing else, so neither this screen nor an administrator
 * can look it up again: if it is lost from here, the account needs a reset, not
 * a lookup. The copy says so rather than implying it can be recovered.
 */
function CredentialsNotice({ created }: { created: Created }) {
  return (
    <Alert tone={created.password ? "error" : "success"}>
      <p className="font-semibold">Cuenta creada para {created.fullName}.</p>
      {created.password ? (
        <>
          <p className="mt-1">
            No se pudo enviar el correo{created.emailError ? ` (${created.emailError})` : ""}. Entrega
            esta contraseña en persona; no vuelve a mostrarse ni se puede consultar después.
          </p>
          <p className="mt-2">
            <code className="select-all rounded bg-surface px-2 py-1 text-base">{created.password}</code>
          </p>
        </>
      ) : (
        <p className="mt-1">Le enviamos la contraseña temporal a {created.email}.</p>
      )}
    </Alert>
  );
}

/** Compact control for use inside a table cell. */
const INLINE_SELECT =
  "rounded-md border border-border bg-surface px-2 py-1.5 text-base text-ink outline-none transition focus:border-brand focus:ring-[3px] focus:ring-brand/[0.12] disabled:cursor-not-allowed disabled:opacity-60";
