import { Link, useParams } from "react-router-dom";
import { ArrowLeft, FileText, MapPin } from "lucide-react";
import { fetchProperty } from "../api/properties";
import StatusBadge from "../components/ui/StatusBadge";
import SectionCard from "../components/ui/SectionCard";
import ErrorState from "../components/ui/ErrorState";
import { DetailSkeleton } from "../components/ui/Skeleton";
import { useApi, esquematicoBadge, fuenteBadge } from "../hooks/useApi";
import { fmtInt, fmtSurface } from "../lib/format";

const FIELDS: { label: string; render: (p: import("../types").Property) => string; mono?: boolean }[] = [
  { label: "Código", render: (p) => p.codigo, mono: true },
  { label: "Dirección", render: (p) => p.direccion },
  { label: "Superficie", render: (p) => `${fmtSurface(p.superficie_m2)} m2` },
  { label: "Capacidad", render: (p) => `${fmtInt(p.capacidad_personas)} pers.` },
  { label: "Estacionamiento", render: (p) => `${fmtInt(p.plazas_estacionamiento)} plazas` },
  { label: "Año de construcción", render: (p) => fmtInt(p.anio_construccion) },
  { label: "Salas / ambientes", render: (p) => fmtInt(p.salas) },
  { label: "Fuente", render: (p) => p.fuente },
  { label: "Última actualización", render: (p) => p.ultima_actualizacion },
];

export default function PropertyDetailPage() {
  const { codigo } = useParams<{ codigo: string }>();
  const result = useApi(() => fetchProperty(codigo ?? ""), [codigo]);
  const property = result.status === "ready" ? result.data : undefined;

  const is404 = result.statusCode === 404;

  return (
    <>
      <Link
        to="/propiedades"
        className="mb-6 inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 transition-colors duration-150 hover:text-slate-900"
      >
        <ArrowLeft size={16} aria-hidden="true" />
        Volver a propiedades
      </Link>

      {result.status === "loading" && <DetailSkeleton />}

      {result.status === "error" && (
        <ErrorState
          title={is404 ? "Propiedad no encontrada" : "No pudimos cargar la propiedad"}
          description={
            is404
              ? "El código solicitado no existe en el portfolio."
              : "Ocurrió un problema al comunicarnos con el servidor."
          }
          detail={is404 ? `${codigo} no figura en el portfolio.` : result.message}
          action={
            is404 ? (
              <Link
                to="/propiedades"
                className="inline-flex h-9 items-center rounded-md border border-slate-300 bg-white px-4 text-sm font-medium text-slate-700 transition-colors duration-150 hover:bg-slate-50"
              >
                Volver a propiedades
              </Link>
            ) : (
              <button
                type="button"
                onClick={result.retry}
                className="inline-flex h-9 items-center rounded-md border border-slate-300 bg-white px-4 text-sm font-medium text-slate-700 transition-colors duration-150 hover:bg-slate-50"
              >
                Reintentar
              </button>
            )
          }
        />
      )}

      {property && (
        <>
          <header className="mb-6">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
                Propiedad {property.codigo}
              </h1>
              <span className="inline-flex items-center gap-1.5 text-sm text-slate-500">
                <MapPin size={15} aria-hidden="true" />
                {property.direccion}
              </span>
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {(() => {
                const e = esquematicoBadge(property.esquematico_generado);
                const f = fuenteBadge(property.fuente);
                return (
                  <>
                    <StatusBadge tone={e.tone}>{e.label}</StatusBadge>
                    <StatusBadge tone={f.tone}>{f.label}</StatusBadge>
                  </>
                );
              })()}
            </div>
          </header>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <SectionCard
              className="xl:col-span-2"
              title="Información general"
              description="Datos técnicos cargados en el portfolio."
            >
              <dl className="grid grid-cols-1 gap-x-6 gap-y-5 sm:grid-cols-2 lg:grid-cols-3">
                {FIELDS.map((field) => (
                  <div key={field.label}>
                    <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{field.label}</dt>
                    <dd
                      className={`mt-1 text-sm ${field.mono ? "font-mono" : ""} font-medium text-slate-900`}
                    >
                      {field.render(property)}
                    </dd>
                  </div>
                ))}
              </dl>
            </SectionCard>

            <SectionCard title="Esquemático" description="Estado del plano técnico generado.">
              <div className="flex items-start gap-3">
                <div
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500"
                  aria-hidden="true"
                >
                  <FileText size={18} />
                </div>
                <div className="min-w-0">
                  {property.archivo_esquematico ? (
                    <>
                      <p className="text-sm font-medium text-slate-900">
                        {property.archivo_esquematico}
                      </p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        Generado para la propiedad {property.codigo}.
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="text-sm font-medium text-slate-900">Sin esquemático generado</p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        Esta propiedad todavía no tiene plano técnico.
                      </p>
                    </>
                  )}
                </div>
              </div>
            </SectionCard>
          </div>
        </>
      )}
    </>
  );
}