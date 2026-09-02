import { cn } from "@/lib/utils";

/**
 * Surface card, ported from the reference `.card`
 * (proyecto_daniela @ 1aa2b0a — global.css:234-252): surface, radius-lg,
 * 1px border, 24px padding, shadow-sm; `h3` at 16px/700; `.muted-title` at
 * 12px uppercase muted 600 with 0.06em tracking.
 */
export function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("rounded-lg border border-border bg-surface p-6 shadow-sm", className)}>
      {children}
    </div>
  );
}

export function CardTitle({ children }: { children: React.ReactNode }) {
  return <h3 className="mb-3 text-lg font-bold text-ink">{children}</h3>;
}

export function CardMutedTitle({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-2 text-xs font-semibold uppercase tracking-[0.06em] text-muted">{children}</p>
  );
}

/** A single vital reading. Same card language, tightened for a metric grid. */
export function VitalCard({
  label,
  value,
  unit,
}: {
  label: string;
  value: string | number;
  unit?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.04em] text-muted">{label}</p>
      <div className="mt-1.5 flex items-end gap-1">
        <p className="text-4xl font-bold text-ink">{value}</p>
        {unit ? <p className="pb-1.5 text-xs font-medium text-muted">{unit}</p> : null}
      </div>
    </div>
  );
}
