import type { KeyboardEvent, ReactNode } from "react";
import { Skeleton } from "./Skeleton";

export interface DataColumn<T> {
  key: string;
  header: string;
  align?: "left" | "right" | "center";
  className?: string;
  render: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: DataColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  ariaLabel: string;
  /** Rows are keyboard-operable when provided. */
  onRowClick?: (row: T) => void;
  loading?: boolean;
  skeletonRows?: number;
  empty?: ReactNode;
}

const ALIGN: Record<string, string> = {
  left: "text-left",
  right: "text-right",
  center: "text-center",
};

export default function DataTable<T>({
  columns,
  rows,
  rowKey,
  ariaLabel,
  onRowClick,
  loading = false,
  skeletonRows = 8,
  empty,
}: DataTableProps<T>) {
  if (loading) {
    return (
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-2.5">
          {columns.map((col) => (
            <span key={col.key} className="inline-block w-24 pr-6 last:hidden">
              <Skeleton className="h-3" />
            </span>
          ))}
        </div>
        {Array.from({ length: skeletonRows }).map((_, r) => (
          <div key={r} className="flex gap-6 border-b border-slate-100 px-4 py-3.5 last:border-0">
            {columns.map((col) => (
              <Skeleton key={col.key} className="h-3.5 flex-1" />
            ))}
          </div>
        ))}
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        {empty ?? (
          <div className="p-8 text-center text-sm text-slate-500">No hay resultados para mostrar.</div>
        )}
      </div>
    );
  }

  return (
    <div className="max-h-[540px] overflow-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full border-collapse text-sm" aria-label={ariaLabel}>
        <thead className="sticky top-0 z-10 bg-white">
          <tr className="border-b border-slate-200">
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={`px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500 ${ALIGN[col.align ?? "left"]}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const key = rowKey(row);
            const interactive = Boolean(onRowClick);
            const rowProps = interactive
              ? {
                  tabIndex: 0,
                  role: "link",
                  "aria-label": ariaLabel,
                  onClick: () => onRowClick?.(row),
                  onKeyDown: (e: KeyboardEvent) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onRowClick?.(row);
                    }
                  },
                }
              : {};
            return (
              <tr
                key={key}
                {...rowProps}
                className={`border-b border-slate-100 last:border-0 transition-colors duration-150 ${
                  interactive ? "cursor-pointer hover:bg-slate-50 focus-visible:bg-slate-50 focus-visible:outline-none" : ""
                }`}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={`px-4 py-3 text-slate-700 ${ALIGN[col.align ?? "left"]} ${col.className ?? ""}`}
                  >
                    {col.render(row)}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}