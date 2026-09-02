"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { LogIn } from "lucide-react";

import { Alert } from "@/components/alerts/alert-row";
import { AuthShell } from "@/components/ui/auth-shell";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { createBrowserSupabaseClient, isSupabaseConfigured } from "@/lib/supabase";
import type { UserRole } from "@/types";

const ROLE_HOME: Record<UserRole, string> = {
  patient: "/patient/dashboard",
  ips: "/ips/dashboard",
  admin: "/admin/dashboard",
};

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginContent />
    </Suspense>
  );
}

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const nextMessage = searchParams.get("message");
    if (nextMessage) {
      setMessage(nextMessage);
    }
  }, [searchParams]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const supabase = createBrowserSupabaseClient();
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        setMessage(error.message);
        return;
      }
      const userId = data.user?.id;
      const { data: profile } = await supabase.from("profiles").select("role").eq("id", userId).single();
      const role = (profile?.role ?? "patient") as UserRole;
      router.push(ROLE_HOME[role]);
    } finally {
      setLoading(false);
    }
  }

  function enterDemo(role: UserRole) {
    router.push(ROLE_HOME[role]);
  }

  return (
    <AuthShell>
      <h1 className="text-3xl font-bold text-ink">Ingreso seguro</h1>
      <p className="mt-1 text-base text-muted">Accede a tu panel de monitoreo clínico.</p>

      {isSupabaseConfigured() ? (
        <form onSubmit={handleSubmit} className="mt-6">
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
          {message ? <Alert tone="error">{message}</Alert> : null}
          <Button type="submit" disabled={loading} full>
            <LogIn className="h-4 w-4" aria-hidden />
            Ingresar
          </Button>
        </form>
      ) : (
        <div className="mt-6 grid gap-2">
          {message ? <Alert tone="error">{message}</Alert> : null}
          <Button type="button" onClick={() => enterDemo("patient")} full>Paciente demo</Button>
          <Button type="button" variant="secondary" onClick={() => enterDemo("ips")} full>IPS demo</Button>
          <Button type="button" variant="secondary" onClick={() => enterDemo("admin")} full>Admin demo</Button>
        </div>
      )}

      <p className="mt-5 text-center text-base text-muted">
        <Link
          href="/register"
          className="font-semibold text-brand outline-none hover:underline focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2"
        >
          Crear usuario
        </Link>
      </p>
    </AuthShell>
  );
}
