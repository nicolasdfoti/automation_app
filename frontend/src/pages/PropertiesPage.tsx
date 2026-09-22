import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchProperties } from "../api/properties";
import type { EstadoFiltro, Property } from "../types";
import { fmtSurface } from "../lib/format";

type State =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; properties: Property[] };

export default function PropertiesPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [fuente, setFuente] = useState("");
  const [estado, setEstado] = useState<EstadoFiltro | "">("");
  const [superficieMin, setSuperficieMin] = useState("");
  const [superficieMax, setSuperficieMax] = useState("");
  const [state, setState] = useState<State>({ status: "loading" });
  const [debounced, setDebounced] = useState("");

  useEffect(() => {
    const t = window.setTimeout(() => setDebounced(search), 300);
    return () => window.clearTimeout(t);
  }, [search]);

  useEffect(() => {
    let cancelled = false;
    setState((prev) => (prev.status === "ready" ? { status: "loading" } : prev));
    fetchProperties({
      search: debounced || undefined,
      fuente: fuente || undefined,
      estado: estado || undefined,
      superficie_min: superficieMin ? Number(superficieMin) : undefined,
      superficie_max: superficieMax ? Number(superficieMax) : undefined,
    })
      .then((res) => {
        if (!cancelled) setState({ status: "ready", properties: res.items });
      })
      .catch((err: Error) => {
        if (!cancelled) setState({ status: "error", message: err.message });
      });
    return () => {
      cancelled = true;
    };
  }, [debounced, fuente, estado, superficieMin, superficieMax]);

  const hasFilters = Boolean(search || fuente || estado || superficieMin || superficieMax);

  return (
    <section>
      <h1 className="mb-6 text-2xl font-semibold text-slate-900">Propiedades</h1>

      <div className="mb-4 flex flex-wrap gap-3">
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar por código o dirección…"
          className="w-72 rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <select
          value={fuente}
          onChange={(e) => setFuente(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">Todas las fuentes</option>
          <option value="carga manual (legacy)">Legacy</option>
          <option value="automatizacion OCR">Automatizado</option>
        </select>
        <select
          value={estado}
          onChange={(e) => setEstado(e.target.value as EstadoFiltro | "")}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">Todos los estados</option>
          <option value="generado">Con esquemático</option>
          <option value="pendiente">Pendiente</option>
        </select>
        <input
          type="number"
          value={superficieMin}
          onChange={(e) => setSuperficieMin(e.target.value)}
          placeholder="Superficie mín"
          className="w-32 rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <input
          type="number"
          value={superficieMax}
          onChange={(e) => setSuperficieMax(e.target.value)}
          placeholder="Superficie máx"
          className="w-32 rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        {hasFilters && (
          <button
            onClick={() => {
              setSearch("");
              setFuente("");
              setEstado("");
              setSuperficieMin("");
              setSuperficieMax("");
            }}
            className="rounded-md px-3 py-2 text-sm text-slate-600 hover:bg-slate-100"
          >
            Limpiar filtros
          </button>
        )}
      </div>

      {state.status === "loading" && <p>Cargando propiedades…</p>}
      {state.status === "error" && <p>No pudimos cargar las propiedades: {state.message}</p>}
      {state.status === "ready" &&
        (state.properties.length === 0 ? (
          <p className="text-sm text-slate-500">No encontramos propiedades con el filtro actual.</p>
        ) : (
          <>
            <p className="mb-2 text-sm text-slate-500">
              {state.properties.length} {state.properties.length === 1 ? "propiedad" : "propiedades"}
            </p>
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-4">Código</th>
                  <th className="py-2 pr-4">Dirección</th>
                  <th className="py-2 pr-4 text-right">Superficie</th>
                  <th className="py-2 pr-4">Estado</th>
                  <th className="py-2 pr-4">Fuente</th>
                </tr>
              </thead>
              <tbody>
                {state.properties.map((p) => (
                  <tr
                    key={p.codigo}
                    onClick={() => navigate(`/propiedades/${p.codigo}`)}
                    className="cursor-pointer border-b border-slate-100 hover:bg-slate-50"
                  >
                    <td className="py-2 pr-4 font-mono text-slate-800">{p.codigo}</td>
                    <td className="py-2 pr-4 text-slate-700">{p.direccion}</td>
                    <td className="py-2 pr-4 text-right text-slate-700">{fmtSurface(p.superficie_m2)}</td>
                    <td className="py-2 pr-4 text-slate-700">
                      {p.esquematico_generado ? "Con esquemático" : "Pendiente"}
                    </td>
                    <td className="py-2 pr-4 text-slate-700">{p.fuente}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ))}
    </section>
  );
}