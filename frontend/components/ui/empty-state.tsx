import { cn } from "@/lib/utils";

/**
 * Empty and loading states, ported from the reference `.empty`, `.spinner`
 * and `.center-wrap` (proyecto_daniela @ 1aa2b0a — global.css:483-507):
 * centred muted 14px text at 40px/20px padding; a 24px ring in primary-light
 * with a primary top edge, spinning at 0.8s.
 */
export function EmptyState({ children }: { children: React.ReactNode }) {
  return <p className="px-5 py-10 text-center text-base text-muted">{children}</p>;
}

export function Spinner({ size = "md", label = "Cargando" }: { size?: "md" | "lg"; label?: string }) {
  return (
    <span
      role="status"
      aria-live="polite"
      className={cn(
        "inline-block animate-spin rounded-full border-brand-light border-t-brand",
        size === "lg" ? "h-10 w-10 border-4" : "h-6 w-6 border-[3px]",
      )}
    >
      <span className="sr-only">{label}</span>
    </span>
  );
}

/** The reference's `.center-wrap`: a centred slot for a spinner or notice. */
export function CenterWrap({ children }: { children: React.ReactNode }) {
  return <div className="flex items-center justify-center px-5 py-14">{children}</div>;
}
