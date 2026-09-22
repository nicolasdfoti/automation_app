import type { ReactNode } from "react";
import { SlidersHorizontal } from "lucide-react";
import { buttonClass } from "./Button";

/** Shared height/shape for raw filter controls (selects, number inputs). */
export const FILTER_INPUT_CLASS =
  "h-9 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900 shadow-sm transition-colors duration-150 hover:border-slate-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20";

interface FilterBarProps {
  /** Label describing the group, e.g. "Filtros de propiedades". */
  label: string;
  activeCount: number;
  onClear: () => void;
  children: ReactNode;
}

export default function FilterBar({ label, activeCount, onClear, children }: FilterBarProps) {
  return (
    <div
      role="group"
      aria-label={label}
      className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
    >
      {children}
      {activeCount > 0 && (
        <div className="ml-auto flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-md bg-primary-50 px-2 py-1 text-xs font-medium text-primary-700">
            <SlidersHorizontal size={13} aria-hidden="true" />
            {activeCount} {activeCount === 1 ? "filtro" : "filtros"} activos
          </span>
          <button type="button" onClick={onClear} className={buttonClass("ghost", "sm")}>
            Limpiar filtros
          </button>
        </div>
      )}
    </div>
  );
}