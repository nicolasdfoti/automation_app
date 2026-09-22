import type { LucideIcon } from "lucide-react";
import type { BadgeTone } from "../../types";

const ICON_TONES: Record<BadgeTone | "primary", string> = {
  primary: "bg-primary-50 text-primary-600",
  success: "bg-success-50 text-success-600",
  warning: "bg-warning-50 text-warning-600",
  error: "bg-error-50 text-error-600",
  neutral: "bg-slate-100 text-slate-600",
  info: "bg-info-50 text-info-600",
};

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  hint?: string;
  tone?: BadgeTone | "primary";
}

export default function StatCard({ icon: Icon, label, value, hint, tone = "neutral" }: StatCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow duration-200 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-3 text-[28px] font-semibold tabular-nums tracking-tight text-slate-900">{value}</p>
        </div>
        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${ICON_TONES[tone]}`}
          aria-hidden="true"
        >
          <Icon size={20} />
        </div>
      </div>
      {hint && <p className="mt-2 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}