import { cn } from "@/lib/utils";

/**
 * Table primitives, ported from the reference `.table-wrap` and its bare
 * `table` / `thead th` / `tbody td` rules
 * (proyecto_daniela @ 1aa2b0a — global.css:392-426): surface, radius-lg,
 * 1px border, shadow-sm, overflow auto; header 12px uppercase muted 600 with
 * 0.04em tracking on the page background; cells 12px/14px with a 1px divider,
 * dropped on the last row; clickable rows tint with primary-soft on hover.
 */
export function TableWrap({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("overflow-auto rounded-lg border border-border bg-surface shadow-sm", className)}>
      {children}
    </div>
  );
}

export function Table({ children }: { children: React.ReactNode }) {
  return <table className="w-full border-collapse text-base">{children}</table>;
}

export function Th({ className, children }: { className?: string; children?: React.ReactNode }) {
  return (
    <th
      scope="col"
      className={cn(
        "border-b border-border bg-canvas px-3.5 py-3 text-left text-xs font-semibold uppercase tracking-[0.04em] text-muted",
        className,
      )}
    >
      {children}
    </th>
  );
}

export function Td({ className, children }: { className?: string; children?: React.ReactNode }) {
  return <td className={cn("px-3.5 py-3", className)}>{children}</td>;
}

export function Tr({
  clickable = false,
  className,
  children,
}: {
  clickable?: boolean;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <tr
      className={cn(
        "border-b border-border last:border-b-0",
        clickable && "cursor-pointer transition-colors hover:bg-brand-soft",
        className,
      )}
    >
      {children}
    </tr>
  );
}
