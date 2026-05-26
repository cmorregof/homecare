"use client";

import { FormEvent, useState } from "react";
import { UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { Profile, UserRole } from "@/types";

export function UserManagement({ initialProfiles }: { initialProfiles: Profile[] }) {
  const [profiles, setProfiles] = useState(initialProfiles);
  const [name, setName] = useState("");
  const [role, setRole] = useState<UserRole>("patient");

  function createUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      return;
    }
    setProfiles((current) => [
      ...current,
      {
        id: `draft-${Date.now()}`,
        full_name: name.trim(),
        role,
      },
    ]);
    setName("");
    setRole("patient");
  }

  function updateRole(id: string, nextRole: UserRole) {
    setProfiles((current) => current.map((profile) => (profile.id === id ? { ...profile, role: nextRole } : profile)));
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
      <form onSubmit={createUser} className="rounded-md border border-slate-200 bg-white p-5">
        <h2 className="font-semibold">Crear usuario</h2>
        <label className="mt-4 block text-sm font-medium text-slate-700">
          Nombre
          <input value={name} onChange={(event) => setName(event.target.value)} className="mt-1 h-11 w-full rounded-md border border-slate-300 px-3" />
        </label>
        <label className="mt-4 block text-sm font-medium text-slate-700">
          Rol
          <select value={role} onChange={(event) => setRole(event.target.value as UserRole)} className="mt-1 h-11 w-full rounded-md border border-slate-300 px-3">
            <option value="patient">Paciente</option>
            <option value="ips">IPS</option>
            <option value="admin">Admin</option>
          </select>
        </label>
        <Button type="submit" className="mt-5 w-full">
          <UserPlus className="h-4 w-4" aria-hidden />
          Crear
        </Button>
      </form>

      <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
        <table className="w-full min-w-[680px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 font-semibold">Usuario</th>
              <th className="px-4 py-3 font-semibold">Rol</th>
              <th className="px-4 py-3 font-semibold">Médico asignado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {profiles.map((profile) => (
              <tr key={profile.id}>
                <td className="px-4 py-3">
                  <p className="font-medium text-ink">{profile.full_name}</p>
                  <p className="text-xs text-slate-500">{profile.document_id ?? profile.email ?? profile.id}</p>
                </td>
                <td className="px-4 py-3">
                  <select value={profile.role} onChange={(event) => updateRole(profile.id, event.target.value as UserRole)} className="h-9 rounded-md border border-slate-300 px-2">
                    <option value="patient">Paciente</option>
                    <option value="ips">IPS</option>
                    <option value="admin">Admin</option>
                  </select>
                </td>
                <td className="px-4 py-3">
                  <select className="h-9 rounded-md border border-slate-300 px-2" defaultValue={profile.assigned_doctor_id ?? ""}>
                    <option value="">Sin asignar</option>
                    {profiles.filter((item) => item.role === "ips").map((doctor) => (
                      <option key={doctor.id} value={doctor.id}>{doctor.full_name}</option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
