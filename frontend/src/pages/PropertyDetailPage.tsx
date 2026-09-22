import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchProperty } from "../api/properties";
import type { Property } from "../types";
import { fmtInt, fmtSurface } from "../lib/format";

type State =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; property: Property };

export default function PropertyDetailPage() {
  const { codigo } = useParams<{ codigo: string }>();
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    if (!codigo) return;
    let cancelled = false;
    setState({ status: "loading" });
    fetchProperty(codigo)
      .then((property) => {
        if (!cancelled) setState({ status: "ready", property });
      })
      .catch((err: Error) => {
        if (!cancelled) setState({ status: "error", message: err.message });
      });
    return () => {
      cancelled = true;
    };
  }, [codigo]);

  return (
    <section>
      <Link to="/propiedades" className="mb-4 inline-flex items-center text-sm text-slate-600 hover:text-slate-900">
        ← Volver a propiedades
      </Link>

      {state.status === "loading" && <p>Cargando propiedad…</p>}
      {state.status === "error" && <p>No pudimos cargar la propiedad: {state.message}</p>}

      {state.status === "ready" && (
        <>
          <h1 className="text-2xl font-semibold text-slate-900">Propiedad {state.property.codigo}</h1>
          <p className="text-sm text-slate-600">{state.property.direccion}</p>

          <p className="mt-2 text-sm">
            {state.property.esquematico_generado ? (
              <span className="font-medium text-emerald-700">Esquemático generado</span>
            ) : (
              <span className="font-medium text-amber-700">Pendiente de esquemático</span>
            )}
          </p>

          <h2 className="mb-2 mt-8 text-lg font-semibold text-slate-900">Información general</h2>
          <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Código</dt>
              <dd className="font-mono text-slate-800">{state.property.codigo}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Dirección</dt>
              <dd className="text-slate-800">{state.property.direccion}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Superficie</dt>
              <dd className="text-slate-800">{fmtSurface(state.property.superficie_m2)} m2</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Capacidad</dt>
              <dd className="text-slate-800">{fmtInt(state.property.capacidad_personas)} pers.</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Estacionamiento</dt>
              <dd className="text-slate-800">{fmtInt(state.property.plazas_estacionamiento)} plazas</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Año de construcción</dt>
              <dd className="text-slate-800">{fmtInt(state.property.anio_construccion)}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Salas</dt>
              <dd className="text-slate-800">{fmtInt(state.property.salas)}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Fuente</dt>
              <dd className="text-slate-800">{state.property.fuente}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Última actualización</dt>
              <dd className="text-slate-800">{state.property.ultima_actualizacion}</dd>
            </div>
          </dl>

          <h2 className="mb-2 mt-8 text-lg font-semibold text-slate-900">Esquemático</h2>
          <p className="text-sm text-slate-600">
            {state.property.archivo_esquematico
              ? `Archivo: ${state.property.archivo_esquematico}`
              : "Esta propiedad todavía no tiene esquemático generado."}
          </p>
        </>
      )}
    </section>
  );
}