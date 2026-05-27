"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { Activity, LogIn } from "lucide-react";

import { Button } from "@/components/ui/button";
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
    <main className="grid min-h-screen place-items-center bg-[#f5f8f7] px-4 py-10 text-ink">
      <section className="w-full max-w-md rounded-md border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-md bg-clinical text-white">
            <Activity aria-hidden />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">HomecareCCV</h1>
            <p className="text-sm text-slate-600">Ingreso seguro</p>
          </div>
        </div>

        {isSupabaseConfigured() ? (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <label className="block text-sm font-medium text-slate-700">
              Correo
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
                required
                className="mt-1 h-11 w-full rounded-md border border-slate-300 px-3 outline-none focus:border-clinical focus:ring-2 focus:ring-teal-100"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Contraseña
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                required
                className="mt-1 h-11 w-full rounded-md border border-slate-300 px-3 outline-none focus:border-clinical focus:ring-2 focus:ring-teal-100"
              />
            </label>
            {message ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{message}</p> : null}
            <Button type="submit" disabled={loading} className="w-full">
              <LogIn className="h-4 w-4" aria-hidden />
              Ingresar
            </Button>
          </form>
        ) : (
          <div className="mt-6 grid gap-2">
            <Button type="button" onClick={() => enterDemo("patient")}>Paciente demo</Button>
            <Button type="button" variant="secondary" onClick={() => enterDemo("ips")}>IPS demo</Button>
            <Button type="button" variant="secondary" onClick={() => enterDemo("admin")}>Admin demo</Button>
          </div>
        )}

        <p className="mt-5 text-center text-sm text-slate-600">
          <Link href="/register" className="font-medium text-clinical">
            Crear usuario
          </Link>
        </p>
      </section>
    </main>
  );
}
