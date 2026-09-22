import { Building2, CheckCircle2, Clock, Ruler } from "lucide-react";
import { fetchProperties, fetchStats } from "../api/properties";
import PageHeader from "../components/ui/PageHeader";
import StatCard from "../components/ui/StatCard";
import StatusBadge from "../components/ui/StatusBadge";
import SectionCard from "../components/ui/SectionCard";
import ErrorState from "../components/ui/ErrorState";
import { ActivityListSkeleton, KPISkeleton } from "../components/ui/Skeleton";
import { useApi, fuenteBadge } from "../hooks/useApi";
import { fmtCapacidad, fmtInt, fmtSurface } from "../lib/format";
import type { Property } from "../types";

function dateValue(value: string): number {
  const [d, m, y] = value.split("/").map(Number);
  return new Date(y, m - 1, d).getTime();
}

function pct(part: number, total: number): number {
  return total === 0 ? 0 : Math.round((part / total) * 100);
}

function ActivityRow({ property }: { property: Property }) {
  const fuente = fuenteBadge(property.fuente);
  return (
    <li className="flex items-center justify-between gap-3 py-2.5">
      <div className="min-w-0">
        <p className="truncate font-mono text-sm font-medium text-slate-900">{property.codigo}</p>
        <p className="truncate text-xs text-slate-500">{property.direccion}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <StatusBadge tone={fuente.tone}>{fuente.label}</StatusBadge>
        <span className="text-xs tabular-nums text-slate-400">{property.ultima_actualizacion}</span>
      </div>
    </li>
  );
}

export default function Dashboard() {
  const stats = useApi(fetchStats, []);
  const activity = useApi(fetchProperties, []);

  const recent: Property[] = (activity.data?.items ?? [])
    .map((p) => ({ ...p, _sort: dateValue(p.ultima_actualizacion) }))
    .sort((a, b) => b._sort - a._sort)
    .slice(0, 8);

  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle="Estado operativo del relevamiento técnico del portfolio."
      />

      {stats.status === "loading" && <KPISkeleton />}

      {stats.status === "error" && (
        <ErrorState
          title="No pudimos cargar los indicadores"
          description="Ocurrió un problema al comunicarnos con el servidor."
          detail={stats.message}
          onRetry={stats.retry}
        />
      )}

      {stats.status === "ready" && stats.data && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              icon={Building2}
              label="Propiedades totales"
              value={fmtInt(stats.data.total)}
              hint={`${fmtInt(stats.data.pendientes)} pendientes de esquemático`}
              tone="primary"
            />
            <StatCard
              icon={Clock}
              label="Pendientes"
              value={fmtInt(stats.data.pendientes)}
              hint={`${pct(stats.data.pendientes, stats.data.total)}% del portfolio`}
              tone="warning"
            />
            <StatCard
              icon={CheckCircle2}
              label="Corregidas"
              value={fmtInt(stats.data.corregidas)}
              hint="vía automatización OCR"
              tone="success"
            />
            <StatCard
              icon={Ruler}
              label="Superficie total"
              value={`${fmtSurface(stats.data.superficie_total)} m2`}
              hint="superficie relevada"
              tone="info"
            />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
            <SectionCard
              className="lg:col-span-2"
              title="Resumen operativo"
              description="Avance del relevamiento técnico y de la automatización."
            >
              <dl className="space-y-5">
                <div>
                  <div className="mb-1.5 flex items-baseline justify-between text-sm">
                    <dt className="font-medium text-slate-700">Automatización</dt>
                    <dd className="tabular-nums text-slate-500">
                      {fmtInt(stats.data.corregidas)} de {fmtInt(stats.data.total)} propiedades (
                      {pct(stats.data.corregidas, stats.data.total)}%)
                    </dd>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-100" role="presentation">
                    <div
                      className="h-full rounded-full bg-success-500 transition-all duration-300 ease-out"
                      style={{ width: `${pct(stats.data.corregidas, stats.data.total)}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="mb-1.5 flex items-baseline justify-between text-sm">
                    <dt className="font-medium text-slate-700">Esquemáticos pendientes</dt>
                    <dd className="tabular-nums text-slate-500">
                      {fmtInt(stats.data.pendientes)} de {fmtInt(stats.data.total)} propiedades (
                      {pct(stats.data.pendientes, stats.data.total)}%)
                    </dd>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-100" role="presentation">
                    <div
                      className="h-full rounded-full bg-warning-500 transition-all duration-300 ease-out"
                      style={{ width: `${pct(stats.data.pendientes, stats.data.total)}%` }}
                    />
                  </div>
                </div>
              </dl>

              <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
                <span className="font-medium text-slate-700">Capacidad total instalada: </span>
                <span className="tabular-nums text-slate-900">{fmtCapacidad(stats.data.capacidad_total)} personas</span>
              </div>
            </SectionCard>

            <SectionCard
              title="Última actividad"
              description="Propiedades más recientemente actualizadas."
            >
              {activity.status === "loading" && <ActivityListSkeleton />}
              {activity.status === "error" && (
                <div className="text-sm text-slate-500">
                  <p>{activity.message}</p>
                  <button
                    type="button"
                    onClick={activity.retry}
                    className="mt-2 text-primary-600 underline-offset-2 hover:underline"
                  >
                    Reintentar
                  </button>
                </div>
              )}
              {activity.status === "ready" && (
                <>
                  <ul className="divide-y divide-slate-100">
                    {recent.map((p) => (
                      <ActivityRow key={p.codigo} property={p} />
                    ))}
                  </ul>
                  {recent.length === 0 && (
                    <p className="py-2 text-sm text-slate-500">Aún no hay propiedades cargadas.</p>
                  )}
                </>
              )}
            </SectionCard>
          </div>
        </>
      )}
    </>
  );
}