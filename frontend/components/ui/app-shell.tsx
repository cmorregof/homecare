"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Bell,
  Bot,
  Database,
  Heart,
  LayoutDashboard,
  LogOut,
  Menu,
  PlusCircle,
  Users,
  X,
  type LucideIcon,
} from "lucide-react";

import { DemoBanner } from "@/components/ui/demo-banner";
import { BRAND_NAME, BRAND_TAGLINE } from "@/lib/brand";
import { signOutAction } from "@/lib/session-actions";
import { PageHeader } from "@/components/ui/page-header";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/types";

/**
 * Application shell, structured after the reference layout
 * (proyecto_daniela @ 1aa2b0a — salud-cardiaca-web/src/components/Layout.jsx
 * and the .app-shell / .sidebar / .nav / .main / .avatar / .user-info rules in
 * its global.css): a fixed sidebar carrying brand, navigation and a user block,
 * with the page body to its right.
 *
 * Three deliberate departures from the reference:
 *
 * 1. Icons are lucide components, not emoji. The reference passes `♥` and `⎋`
 *    as strings through `l.icon`; here the icon is typed as a LucideIcon.
 * 2. Navigation is per-role. The reference knows two roles and hardcodes the
 *    link list; we resolve it from the role the middleware already enforced.
 * 3. Mobile is an off-canvas drawer. The reference simply hides the sidebar
 *    below 800px (`.sidebar { display: none }`), which leaves navigation
 *    unreachable on a phone. The drawer keeps one navigation definition and
 *    one set of behaviours at every width.
 */

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

const NAV_ITEMS: Record<UserRole, NavItem[]> = {
  patient: [
    { href: "/patient/dashboard", label: "Panel", icon: LayoutDashboard },
    { href: "/patient/vitals/new", label: "Nueva medición", icon: PlusCircle },
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

const ROLE_LABEL: Record<UserRole, string> = {
  patient: "Paciente",
  ips: "IPS",
  admin: "Administrador",
};

/** Ring used on every focusable control so keyboard focus is always visible. */
const FOCUS_RING =
  "outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-surface";

function isCurrent(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

function SidebarBody({
  role,
  userName,
  pathname,
  onNavigate,
}: {
  role: UserRole;
  userName?: string;
  pathname: string;
  onNavigate?: () => void;
}) {
  const initial = (userName?.trim() || ROLE_LABEL[role]).slice(0, 1).toUpperCase();

  return (
    <>
      <div className="mb-8 flex items-center gap-2.5 px-2">
        <Heart className="h-6 w-6 shrink-0 fill-current text-brand" aria-hidden />
        <span className="flex min-w-0 flex-col leading-tight">
          <span className="text-xl font-extrabold text-ink">{BRAND_NAME}</span>
          <span className="text-xs text-muted">{BRAND_TAGLINE}</span>
        </span>
      </div>

      <nav aria-label="Navegación principal" className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS[role].map((item) => {
          const Icon = item.icon;
          const current = isCurrent(pathname, item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={current ? "page" : undefined}
              className={cn(
                "flex items-center gap-2.5 rounded-md px-3 py-2.5 text-base transition-colors",
                FOCUS_RING,
                current
                  ? "bg-brand-soft font-semibold text-brand-dark"
                  : "font-medium text-muted hover:bg-canvas hover:text-ink",
              )}
            >
              <Icon className="h-[18px] w-[18px] shrink-0" aria-hidden />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-4 border-t border-border pt-4">
        <div className="flex items-center gap-3">
          <div
            className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-brand text-base font-bold text-white"
            aria-hidden
          >
            {initial}
          </div>
          <div className="min-w-0 flex-1">
            {userName ? (
              <p className="truncate text-sm font-semibold text-ink">{userName}</p>
            ) : null}
            <p className="text-[11px] uppercase tracking-[0.04em] text-muted">
              {ROLE_LABEL[role]}
            </p>
          </div>
        </div>
        <SignOutButton className="mt-3 w-full justify-center" />
      </div>
    </>
  );
}

/**
 * Sign-out control.
 *
 * Written out rather than an icon tile because the icon-only version was the
 * whole problem: a 36px square whose only label was `sr-only`, parked in the
 * sidebar footer, which on a phone means opening the drawer first. The label is
 * visible at every width, and the same component sits in the mobile bar so
 * leaving takes one tap.
 *
 * It is a form, not a link. See lib/session-actions.ts for why the link it
 * replaces never actually ended the session.
 */
function SignOutButton({ className }: { className?: string }) {
  return (
    <form action={signOutAction}>
      <button
        type="submit"
        className={cn(
          "flex items-center gap-2 rounded-md px-3 py-2.5 text-base font-medium text-muted transition-colors",
          "hover:bg-canvas hover:text-danger",
          FOCUS_RING,
          className,
        )}
      >
        <LogOut className="h-[18px] w-[18px] shrink-0" aria-hidden />
        Cerrar sesión
      </button>
    </form>
  );
}

export function AppShell({
  role,
  title,
  subtitle,
  actions,
  userName,
  children,
}: {
  role: UserRole;
  title: string;
  subtitle?: string;
  /** Controls rendered on the right of the page header. */
  actions?: React.ReactNode;
  /**
   * Display name for the user block. Every role page passes the profile it
   * already loaded through `requireRole`, so the block shows the person rather
   * than the word "PACIENTE". Optional so a page without a profile still
   * renders; it falls back to the role label alone.
   */
  userName?: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Close the drawer on navigation and on Escape.
  useEffect(() => {
    setDrawerOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!drawerOpen) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setDrawerOpen(false);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [drawerOpen]);

  return (
    <div className="min-h-screen bg-canvas text-ink lg:grid lg:grid-cols-[260px_1fr]">
      {/* Desktop sidebar */}
      <aside className="hidden border-r border-border bg-surface px-4 py-6 lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col">
        <SidebarBody role={role} userName={userName} pathname={pathname} />
      </aside>

      {/* Mobile bar */}
      <div className="sticky top-0 z-30 flex items-center gap-3 border-b border-border bg-surface px-4 py-3 lg:hidden">
        <button
          type="button"
          onClick={() => setDrawerOpen(true)}
          aria-label="Abrir navegación"
          aria-expanded={drawerOpen}
          aria-controls="app-shell-drawer"
          className={cn(
            "grid h-9 w-9 shrink-0 place-items-center rounded-md text-muted transition-colors hover:bg-canvas hover:text-ink",
            FOCUS_RING,
          )}
        >
          <Menu className="h-5 w-5" aria-hidden />
        </button>
        <Heart className="h-5 w-5 shrink-0 fill-current text-brand" aria-hidden />
        <span className="truncate text-base font-extrabold text-ink">{BRAND_NAME}</span>
        <SignOutButton className="ml-auto shrink-0 px-2 py-1.5 text-sm" />
      </div>

      {/* Mobile drawer */}
      {drawerOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            tabIndex={-1}
            aria-label="Cerrar navegación"
            onClick={() => setDrawerOpen(false)}
            className="absolute inset-0 h-full w-full cursor-default bg-ink/40"
          />
          <aside
            id="app-shell-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Navegación"
            className="relative flex h-full w-[260px] max-w-[85vw] flex-col border-r border-border bg-surface px-4 py-6 shadow-lg"
          >
            <button
              type="button"
              onClick={() => setDrawerOpen(false)}
              aria-label="Cerrar navegación"
              className={cn(
                "absolute right-3 top-3 grid h-9 w-9 place-items-center rounded-md text-muted transition-colors hover:bg-canvas hover:text-ink",
                FOCUS_RING,
              )}
            >
              <X className="h-5 w-5" aria-hidden />
            </button>
            <SidebarBody
              role={role}
              userName={userName}
              pathname={pathname}
              onNavigate={() => setDrawerOpen(false)}
            />
          </aside>
        </div>
      ) : null}

      <div className="lg:col-start-2">
        <DemoBanner role={role} />
        <main className="overflow-x-auto p-4 lg:px-10 lg:py-8">
          <PageHeader title={title} subtitle={subtitle} actions={actions} />
          {children}
        </main>
      </div>
    </div>
  );
}
