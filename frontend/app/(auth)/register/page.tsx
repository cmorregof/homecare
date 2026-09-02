"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { UserPlus } from "lucide-react";

import { Alert } from "@/components/alerts/alert-row";
import { AuthShell } from "@/components/ui/auth-shell";
import { Button } from "@/components/ui/button";
import { Field, FieldRow, SelectField } from "@/components/ui/field";
import { BRAND_NAME } from "@/lib/brand";
import { getAuthCallbackUrl } from "@/lib/site-url";
import { createBrowserSupabaseClient, isSupabaseConfigured } from "@/lib/supabase";
import type { UserRole } from "@/types";

const ROLE_HOME: Record<UserRole, string> = {
  patient: "/patient/dashboard",
  ips: "/ips/dashboard",
  admin: "/admin/dashboard",
};

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
        router.push(ROLE_HOME[role]);
        return;
      }
      const params = new URLSearchParams({
        message: `Revisa tu correo y confirma la cuenta para ingresar a ${BRAND_NAME}.`,
      });
      router.push(`/login?${params.toString()}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell wide>
      <h1 className="text-3xl font-bold text-ink">Crear cuenta en {BRAND_NAME}</h1>
      <p className="mt-1 text-base text-muted">Crea la cuenta con la que harás seguimiento.</p>

      <form onSubmit={handleSubmit} className="mt-6">
        <Field
          label="Nombre completo"
          required
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
        />
        <FieldRow>
          <Field
            label="Documento"
            required
            value={documentId}
            onChange={(event) => setDocumentId(event.target.value)}
          />
          <SelectField label="Rol" value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
            <option value="patient">Paciente</option>
            <option value="ips">IPS</option>
            <option value="admin">Admin</option>
          </SelectField>
        </FieldRow>
        <FieldRow>
          <Field
            label="Correo"
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <Field
            label="Contraseña"
            type="password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </FieldRow>
        {message ? <Alert tone="error">{message}</Alert> : null}
        <Button type="submit" disabled={loading} full>
          <UserPlus className="h-4 w-4" aria-hidden />
          Crear cuenta
        </Button>
      </form>

      <p className="mt-5 text-center text-base text-muted">
        <Link
          href="/login"
          className="font-semibold text-brand outline-none hover:underline focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2"
        >
          Ya tengo cuenta
        </Link>
      </p>
    </AuthShell>
  );
}
