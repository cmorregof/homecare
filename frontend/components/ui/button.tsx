import { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

/**
 * Button, ported from the reference `.btn`
 * (proyecto_daniela @ 1aa2b0a — global.css:254-285): inline-flex, 8px gap,
 * 10px/18px padding, radius-md, weight 600, 14px, opacity on hover, 1px
 * translate on press, half opacity when disabled.
 *
 * `secondary` is ours, not the reference's: it keeps the neutral outline the
 * existing markup already relies on. The reference's own `.btn.outline` is
 * brand-coloured and is exposed here as `outline`.
 */
type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md";
  full?: boolean;
};

const VARIANTS: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "border-transparent bg-brand text-white hover:opacity-[0.92]",
  secondary: "border-border bg-surface text-ink hover:bg-canvas",
  outline: "border-brand bg-transparent text-brand hover:bg-brand-soft",
  ghost: "border-transparent bg-transparent text-ink hover:bg-canvas",
  danger: "border-transparent bg-danger text-white hover:opacity-[0.92]",
};

const SIZES: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-[18px] py-2.5 text-base",
};

export function Button({
  className,
  variant = "primary",
  size = "md",
  full = false,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md border font-semibold transition",
        "outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-surface",
        "active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50 disabled:active:translate-y-0",
        VARIANTS[variant],
        SIZES[size],
        full && "w-full",
        className,
      )}
      {...props}
    />
  );
}
