import { Link } from "react-router-dom";
import { AlertTriangle, ArrowRight, CheckCircle2, Gauge, SearchX } from "lucide-react";
import { fetchCompare } from "../api/compare";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import StatCard from "../components/ui/StatCard";
import StatusBadge from "../components/ui/StatusBadge";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import DataTable, { type DataColumn } from "../components/ui/DataTable";
import { KPISkeleton, TableSkeleton } from "../components/ui/Skeleton";
import { useApi } from "../hooks/useApi";
import { fmtInt, fmtSurface } from "../lib/format";
import { propertyUrlInTarget } from "../lib/target";
import type { CompareItem, CompareResponse, CompareStatus } from "../types";

const CAMPO_META: Record<string, { label: string; unit: string }> = {
  superficie_m2: { label: "Superficie", unit: " m²" },
  capacidad_personas: { label: "Capacidad", unit: " pers." },
  plazas_estacionamiento: { label: "Estacionamiento", unit: " u." },
  anio_construccion: { label: "Año", unit: "" },
  salas: { label: "Salas", unit: " u." },
};

function statusBadge(status: CompareStatus): { tone: "success" | "warning" | "neutral"; label: string } {
  switch (status) {
    case "coincide":
      return { tone: "success", label: "Coincide" };
    case "diferencia":
      return { tone: "warning", label: "Diferencia" };
    default:
      return { tone: "neutral", label: "Sin datos" };
  }
}

function formatValue(campo: string, value: number | null): string {
  const meta = CAMPO_META[campo] ?? { label: campo, unit: "" };
  if (value == null) return "—";
  const formatted = campo === "superficie_m2" ? fmtSurface(value) : fmtInt(value);
  return `${formatted}${meta.unit}`;
}

function DifferencesCell({ item }: { item: CompareItem }) {
  if (item.status === "coincide") {
    return <span className="text-sm text-slate-500">Todos los campos coinciden.</span>;
  }
  if (item.status === "sin_datos") {
    return <span className="text-sm text-slate-500">Sin datos de OCR para comparar.</span>;
  }
  const differing = item.fields.filter((f) => f.coinciden === false);
  if (differing.length === 0) {
    return <span className="text-sm text-slate-500">No hay campos con diferencia.</span>;
  }
  return (
    <div className="space-y-1.5">
      {differing.map((field) => (
        <div key={field.campo} className="flex items-center gap-2 text-xs">
          <span className="w-28 shrink-0 font-medium text-slate-600">
            {CAMPO_META[field.campo]?.label ?? field.campo}
          </span>
          <span className="text-slate-400">Ref.</span>
          <span className="font-mono tabular-nums text-slate-700">
            {formatValue(field.campo, field.ground_truth)}
          </span>
          <span className="text-slate-400">→</span>
          <span className="text-slate-400">OCR</span>
          <span className="font-mono tabular-nums text-slate-900">
            {formatValue(field.campo, field.ocr)}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function ComparePage() {
  const result = useApi<CompareResponse>(fetchCompare, []);
  const data = result.data;

  const columns: DataColumn<CompareItem>[] = [
    {
      key: "codigo",
      header: "Código",
      className: "whitespace-nowrap font-mono font-medium text-slate-900",
      render: (item) => item.codigo,
    },
    {
      key: "estado",
      header: "Estado",
      render: (item) => {
        const badge = statusBadge(item.status);
        return <StatusBadge tone={badge.tone}>{badge.label}</StatusBadge>;
      },
    },
    {
      key: "detalle",
      header: "Detalle de la comparación",
      render: (item) => <DifferencesCell item={item} />,
    },
    {
      key: "accion",
      header: "Acción",
      align: "right",
      className: "w-36",
      render: (item) => (
        <a
          href={propertyUrlInTarget(item.codigo)}
          target="_blank"
          rel="noreferrer"
          className="inline-flex h-8 items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 text-xs font-medium text-slate-700 transition-colors duration-150 hover:bg-slate-50 hover:text-slate-900"
        >
          Ver propiedad
          <ArrowRight size={13} aria-hidden="true" />
        </a>
      ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Comparar"
        subtitle="Compará los datos detectados por OCR con la información de referencia."
      />

      {result.status === "loading" && (
        <div className="space-y-6">
          <KPISkeleton count={4} />
          <TableSkeleton rows={12} columns={4} />
        </div>
      )}

      {result.status === "error" && (
        <ErrorState
          title="No pudimos cargar la comparación"
          description="Ocurrió un problema al comunicarnos con el servidor."
          detail={result.message}
          onRetry={result.retry}
        />
      )}

      {result.status === "ready" && data && (
        <>
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard icon={Gauge} label="Propiedades comparadas" value={String(data.total)} hint={`${data.sin_datos} sin datos de OCR`} tone="info" />
            <StatCard icon={CheckCircle2} label="Coinciden" value={String(data.coinciden)} tone="success" />
            <StatCard icon={AlertTriangle} label="Diferencias" value={String(data.diferencias)} hint={`${data.propiedades_con_error} propiedades con error`} tone="warning" />
            <StatCard icon={CheckCircle2} label="Exactitud global" value={`${data.exactitud_global}%`} hint="campos correctos / total" tone="primary" />
          </div>

          {data.per_field.length > 0 && (
            <SectionCard className="mb-6" title="Exactitud por campo" description="Qué tan bien leyó el OCR cada campo.">
              <div className="space-y-4">
                {data.per_field.map((field) => {
                  const meta = CAMPO_META[field.campo] ?? { label: field.campo, unit: "" };
                  const pct = Math.max(0, Math.min(100, field.exactitud));
                  return (
                    <div key={field.campo}>
                      <div className="mb-1.5 flex items-center justify-between text-sm">
                        <span className="font-medium text-slate-700">{meta.label}</span>
                        <span className="tabular-nums text-slate-500">{field.exactitud}%</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-slate-200" aria-hidden="true">
                        <div
                          className="h-full rounded-full"
                          style={{ width: `${pct}%`, backgroundColor: "var(--color-success-500)" }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </SectionCard>
          )}

          <SectionCard title="Detalle por propiedad" description="Estado de cada código comparado contra el ground truth.">
            {data.items.length === 0 ? (
              <EmptyState
                icon={SearchX}
                title="Todavía no hay nada para comparar"
                description="Necesitás esquemáticos generados (con su ground truth) y haber corrido el OCR sobre ellos."
                action={
                  <Link
                    to="/ocr"
                    className="inline-flex h-9 items-center rounded-md border border-slate-300 bg-white px-4 text-sm font-medium text-slate-700 transition-colors duration-150 hover:bg-slate-50"
                  >
                    Ir a Correr OCR
                  </Link>
                }
              />
            ) : (
              <DataTable
                columns={columns}
                rows={data.items}
                rowKey={(item) => item.codigo}
                ariaLabel="Comparación de OCR contra ground truth por propiedad"
              />
            )}
          </SectionCard>
        </>
      )}
    </>
  );
}