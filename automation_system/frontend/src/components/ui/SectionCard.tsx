import type { ReactNode } from "react";

interface SectionCardProps {
  title?: string;
  description?: string;
  action?: ReactNode;
  flush?: boolean;
  className?: string;
  children: ReactNode;
}

export default function SectionCard({
  title,
  description,
  action,
  flush = false,
  className,
  children,
}: SectionCardProps) {
  return (
    <section className={`rounded-xl border border-slate-200 bg-white shadow-sm ${className ?? ""}`}>
      {(title || action) && (
        <header className="flex items-start justify-between gap-4 px-6 py-4">
          <div>
            {title && <h2 className="text-base font-semibold text-slate-900">{title}</h2>}
            {description && <p className="mt-0.5 text-sm text-slate-500">{description}</p>}
          </div>
          {action}
        </header>
      )}
      <div className={flush ? "" : "p-6"}>{children}</div>
    </section>
  );
}