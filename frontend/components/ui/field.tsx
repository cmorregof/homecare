"use client";

import { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes, useId } from "react";

import { cn } from "@/lib/utils";

/**
 * Form primitives, ported from the reference `.field`, `.switch-row` and
 * `.switch-toggle` (proyecto_daniela @ 1aa2b0a — global.css:287-368):
 * label 13px/600, helper and error 12px, control with 10px/12px padding,
 * radius-md, 1px border, and a 3px focus ring at 12% of the primary.
 *
 * The reference's focus ring is red because its primary is red; here it is
 * brand blue, since red is reserved for risk.
 */
const CONTROL = cn(
  "w-full rounded-md border border-border bg-surface px-3 py-2.5 text-base text-ink outline-none transition",
  "focus:border-brand focus:ring-[3px] focus:ring-brand/[0.12]",
  "disabled:cursor-not-allowed disabled:opacity-60",
);

const CONTROL_ERROR = "border-danger focus:border-danger focus:ring-danger/[0.12]";

function FieldFrame({
  id,
  label,
  helper,
  error,
  children,
}: {
  id: string;
  label?: string;
  helper?: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-3.5">
      {label ? (
        <label htmlFor={id} className="mb-1.5 block text-sm font-semibold text-ink">
          {label}
        </label>
      ) : null}
      {children}
      {helper && !error ? <p className="mt-1 text-xs text-muted">{helper}</p> : null}
      {error ? (
        <p id={`${id}-error`} className="mt-1 text-xs text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}

type FieldExtras = { label?: string; helper?: string; error?: string };

export function Field({
  label,
  helper,
  error,
  className,
  id,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & FieldExtras) {
  const generated = useId();
  const fieldId = id ?? generated;
  return (
    <FieldFrame id={fieldId} label={label} helper={helper} error={error}>
      <input
        id={fieldId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${fieldId}-error` : undefined}
        className={cn(CONTROL, error && CONTROL_ERROR, className)}
        {...props}
      />
    </FieldFrame>
  );
}

export function SelectField({
  label,
  helper,
  error,
  className,
  id,
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & FieldExtras) {
  const generated = useId();
  const fieldId = id ?? generated;
  return (
    <FieldFrame id={fieldId} label={label} helper={helper} error={error}>
      <select
        id={fieldId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${fieldId}-error` : undefined}
        className={cn(CONTROL, error && CONTROL_ERROR, className)}
        {...props}
      >
        {children}
      </select>
    </FieldFrame>
  );
}

export function TextareaField({
  label,
  helper,
  error,
  className,
  id,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement> & FieldExtras) {
  const generated = useId();
  const fieldId = id ?? generated;
  return (
    <FieldFrame id={fieldId} label={label} helper={helper} error={error}>
      <textarea
        id={fieldId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${fieldId}-error` : undefined}
        className={cn(CONTROL, error && CONTROL_ERROR, className)}
        {...props}
      />
    </FieldFrame>
  );
}

/** The reference's `.row-2` / `.row-3`: equal columns that stack under 600px. */
export function FieldRow({ cols = 2, children }: { cols?: 2 | 3; children: React.ReactNode }) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 gap-3",
        cols === 2 ? "sm:grid-cols-2" : "sm:grid-cols-3",
      )}
    >
      {children}
    </div>
  );
}

/**
 * The reference's `.switch-row` + `.switch-toggle`: a 40x22 pill with an
 * 18px knob. Built on a real checkbox so it is reachable and toggleable by
 * keyboard, which the reference's div-based toggle is not.
 */
export function SwitchRow({
  label,
  checked,
  onChange,
  disabled,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label
      className={cn(
        "mb-2 flex cursor-pointer items-center gap-3 rounded-md border border-border bg-surface px-3.5 py-2.5",
        "focus-within:ring-2 focus-within:ring-brand focus-within:ring-offset-2 focus-within:ring-offset-surface",
        disabled && "cursor-not-allowed opacity-60",
      )}
    >
      <span className="flex-1 text-base font-medium text-ink">{label}</span>
      <input
        type="checkbox"
        role="switch"
        className="peer sr-only"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span
        aria-hidden
        className={cn(
          "relative h-[22px] w-10 shrink-0 rounded-full transition-colors",
          checked ? "bg-brand" : "bg-[#D1D5DB]",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 h-[18px] w-[18px] rounded-full bg-white transition-[left]",
            checked ? "left-5" : "left-0.5",
          )}
        />
      </span>
    </label>
  );
}
