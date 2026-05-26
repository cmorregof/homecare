import Link from "next/link";
import { Activity, Bell, Bot, Database, LayoutDashboard, LogOut, Users, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import type { UserRole } from "@/types";

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

const NAV_ITEMS: Record<UserRole, NavItem[]> = {
  patient: [
    { href: "/patient/dashboard", label: "Panel", icon: LayoutDashboard },
    { href: "/patient/history", label: "Historial", icon: Activity },
    { href: "/patient/chat", label: "Chat", icon: Bot },
  ],
  ips: [
    { href: "/ips/dashboard", label: "Panel", icon: LayoutDashboard },
    { href: "/ips/patients", label: "Pacientes", icon: Users },
    { href: "/ips/alerts", label: "Alertas", icon: Bell },
    { href: "/ips/chat", label: "Chat", icon: Bot },
  ],
  admin: [
    { href: "/admin/dashboard", label: "Panel", icon: LayoutDashboard },
    { href: "/admin/users", label: "Usuarios", icon: Users },
    { href: "/admin/models", label: "Modelos", icon: Activity },
    { href: "/admin/rag", label: "RAG", icon: Database },
  ],
};

export function AppShell({
  role,
  title,
  subtitle,
  children,
}: {
  role: UserRole;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#f5f8f7] text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:block">
        <div className="flex h-16 items-center gap-3 border-b border-slate-200 px-5">
          <div className="grid h-10 w-10 place-items-center rounded-md bg-clinical text-white">
            <Activity aria-hidden />
          </div>
          <div>
            <p className="text-base font-semibold">HomecareCCV</p>
            <p className="text-xs text-slate-500">Monitoreo clínico</p>
          </div>
        </div>
        <nav className="space-y-1 px-3 py-4">
          {NAV_ITEMS[role].map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
              >
                <Icon className="h-4 w-4" aria-hidden />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
          <div className="flex min-h-16 flex-col justify-center gap-1 px-4 py-3 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h1 className="text-xl font-semibold tracking-normal text-ink sm:text-2xl">{title}</h1>
                {subtitle ? <p className="mt-1 text-sm text-slate-600">{subtitle}</p> : null}
              </div>
              <Link
                href="/login"
                className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-200 px-3 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
              >
                <LogOut className="h-4 w-4" aria-hidden />
                Salir
              </Link>
            </div>
            <nav className="flex gap-2 overflow-x-auto pt-2 lg:hidden">
              {NAV_ITEMS[role].map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "inline-flex h-9 shrink-0 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 text-sm",
                    )}
                  >
                    <Icon className="h-4 w-4" aria-hidden />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </header>
        <main className="px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
