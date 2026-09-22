import type { ReactNode } from "react";
import type { BadgeTone } from "../../types";

const TONES: Record<BadgeTone, string> = {
  success: "bg-success-50 text-success-700",
  warning: "bg-warning-50 text-warning-700",
  error: "bg-error-50 text-error-700",
  neutral: "bg-slate-100 text-slate-600",
  info: "bg-info-50 text-info-700",
};

interface StatusBadgeProps {
  tone: BadgeTone;
  children: ReactNode;
}

export default function StatusBadge({ tone, children }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium ${TONES[tone]}`}
    >
      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-current" aria-hidden="true" />
      {children}
    </span>
  );
}