import type { ReactNode } from "react";
import { AlertTriangle } from "lucide-react";
import Button from "./Button";

interface ErrorStateProps {
  title?: string;
  description?: string;
  /** Muted technical detail (e.g. HTTP status). Never a stack trace. */
  detail?: string;
  onRetry?: () => void;
  /** Custom action rendered next to / instead of retry. */
  action?: ReactNode;
}

export default function ErrorState({
  title = "No pudimos cargar la información",
  description = "Ocurrió un problema al comunicarnos con el servidor.",
  detail,
  onRetry,
  action,
}: ErrorStateProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-error-50 text-error-600" aria-hidden="true">
        <AlertTriangle size={22} />
      </div>
      <h3 className="mt-4 text-base font-semibold text-slate-900">{title}</h3>
      <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">{description}</p>
      {detail && <p className="mt-2 text-xs text-slate-400">{detail}</p>}
      <div className="mt-5">
        {action ?? (onRetry && <Button variant="secondary" onClick={onRetry}>Reintentar</Button>)}
      </div>
    </div>
  );
}