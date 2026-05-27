"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { getAuthCallbackUrl } from "@/lib/site-url";
import { createBrowserSupabaseClient, isSupabaseConfigured } from "@/lib/supabase";
import type { UserRole } from "@/types";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("patient");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isSupabaseConfigured()) {
      setMessage("Modo demo activo. Configura Supabase para crear usuarios reales.");
      return;
    }
    setLoading(true);
    try {
      const supabase = createBrowserSupabaseClient();
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: getAuthCallbackUrl(),
          data: {
            full_name: fullName,
            document_id: documentId,
            role,
          },
        },
      });
      if (error) {
        setMessage(error.message);
        return;
      }
      if (data.session && data.user?.id) {
        const { error: profileError } = await supabase.from("profiles").upsert({
          id: data.user.id,
          full_name: fullName,
          document_id: documentId,
          role,
        });
        if (profileError) {
          setMessage(profileError.message);
          return;
        }
      }
      const params = new URLSearchParams({
        message: "Revisa tu correo y confirma la cuenta para ingresar a HomecareCCV.",
      });
      router.push(`/login?${params.toString()}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-[#f5f8f7] px-4 py-10 text-ink">
      <section className="w-full max-w-xl rounded-md border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold tracking-normal">Registro HomecareCCV</h1>
        <form onSubmit={handleSubmit} className="mt-6 grid gap-4 sm:grid-cols-2">
          <label className="block text-sm font-medium text-slate-700 sm:col-span-2">
            Nombre completo
            <input className="mt-1 h-11 w-full rounded-md border border-slate-300 px-3" value={fullName} onChange={(event) => setFullName(event.target.value)} required />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Documento
            <input className="mt-1 h-11 w-full rounded-md border border-slate-300 px-3" value={documentId} onChange={(event) => setDocumentId(event.target.value)} required />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Rol
            <select className="mt-1 h-11 w-full rounded-md border border-slate-300 px-3" value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
              <option value="patient">Paciente</option>
              <option value="ips">IPS</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Correo
            <input className="mt-1 h-11 w-full rounded-md border border-slate-300 px-3" value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Contraseña
            <input className="mt-1 h-11 w-full rounded-md border border-slate-300 px-3" value={password} onChange={(event) => setPassword(event.target.value)} type="password" required />
          </label>
          {message ? <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800 sm:col-span-2">{message}</p> : null}
          <div className="flex items-center justify-between gap-3 sm:col-span-2">
            <Link href="/login" className="text-sm font-medium text-clinical">Volver</Link>
            <Button type="submit" disabled={loading}>Crear cuenta</Button>
          </div>
        </form>
      </section>
    </main>
  );
}
