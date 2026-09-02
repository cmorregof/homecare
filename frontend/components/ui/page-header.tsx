import { cn } from "@/lib/utils";

/**
 * Page furniture, ported from the reference `.page-header`, `.section-title`
 * and `.toolbar` (proyecto_daniela @ 1aa2b0a — global.css:328-344, 509-526):
 * header is a wrapping row aligned to the baseline with a 28px/700 title and
 * a 14px muted subtitle; section titles are 13px uppercase muted 700 with
 * 0.06em tracking; toolbars wrap with a 12px gap and align to the bottom.
 */
export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}) {
  return (
    <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-3xl font-bold text-ink">{title}</h1>
        {subtitle ? <p className="mt-1 text-base text-muted">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex gap-2">{actions}</div> : null}
    </header>
  );
}

export function SectionTitle({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <h2 className={cn("mb-2 mt-6 text-sm font-bold uppercase tracking-[0.06em] text-muted", className)}>
      {children}
    </h2>
  );
}

export function Toolbar({ children }: { children: React.ReactNode }) {
  return <div className="mb-4 flex flex-wrap items-end gap-3">{children}</div>;
}
