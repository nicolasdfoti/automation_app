import type { ReactNode } from "react";

const FIELD_INPUT_CLASS =
  "h-9 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900 shadow-sm transition-colors duration-150 hover:border-slate-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 disabled:bg-slate-50 disabled:text-slate-500";

interface FieldProps {
  /** Stable id/name target for the input (kept predictable for automation). */
  id: string;
  label: string;
  hint?: string;
  error?: string;
  /** Rendered next to the input, e.g. "m2", "pers." */
  suffix?: string;
  children: ReactNode;
  className?: string;
}

export default function Field({
  id,
  label,
  hint,
  error,
  suffix,
  children,
  className,
}: FieldProps) {
  return (
    <div className={className}>
      <label htmlFor={id} className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </label>
      <div className="mt-1 flex items-center gap-2">
        {children}
        {suffix && <span className="shrink-0 text-xs text-slate-500">{suffix}</span>}
      </div>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
      {error && <p className="mt-1 text-xs text-error-600">{error}</p>}
    </div>
  );
}

export { FIELD_INPUT_CLASS };