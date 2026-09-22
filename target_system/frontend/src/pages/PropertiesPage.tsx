import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronRight, SearchX } from "lucide-react";
import { fetchProperties } from "../api/properties";
import PageHeader from "../components/ui/PageHeader";
import SearchInput from "../components/ui/SearchInput";
import FilterBar, { FILTER_INPUT_CLASS } from "../components/ui/FilterBar";
import DataTable, { type DataColumn } from "../components/ui/DataTable";
import StatusBadge from "../components/ui/StatusBadge";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import Button from "../components/ui/Button";
import { TableSkeleton } from "../components/ui/Skeleton";
import { useApi, esquematicoBadge, fuenteBadge } from "../hooks/useApi";
import { fmtSurface } from "../lib/format";
import type { EstadoFiltro, Property } from "../types";

export default function PropertiesPage() {
  const navigate = useNavigate();

  const [searchInput, setSearchInput] = useState("");
  const [debounced, setDebounced] = useState("");
  const [fuente, setFuente] = useState("");
  const [estado, setEstado] = useState<EstadoFiltro | "">("");
  const [minStr, setMinStr] = useState("");
  const [maxStr, setMaxStr] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(searchInput), 300);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const query = useMemo(
    () => ({
      search: debounced || undefined,
      fuente: fuente || undefined,
      estado: estado || undefined,
      superficie_min: minStr ? Number(minStr) : undefined,
      superficie_max: maxStr ? Number(maxStr) : undefined,
    }),
    [debounced, fuente, estado, minStr, maxStr],
  );

  const result = useApi(
    () => fetchProperties(query),
    [query.search, query.fuente, query.estado, query.superficie_min, query.superficie_max],
  );

  const activeCount =
    (searchInput ? 1 : 0) +
    (fuente ? 1 : 0) +
    (estado ? 1 : 0) +
    (minStr ? 1 : 0) +
    (maxStr ? 1 : 0);

  const clearFilters = () => {
    setSearchInput("");
    setFuente("");
    setEstado("");
    setMinStr("");
    setMaxStr("");
  };

  const columns: DataColumn<Property>[] = useMemo(
    () => [
      {
        key: "codigo",
        header: "Código",
        className: "whitespace-nowrap font-mono font-medium text-slate-900",
        render: (p) => p.codigo,
      },
      {
        key: "direccion",
        header: "Dirección",
        className: "max-w-xs truncate text-slate-700",
        render: (p) => <span className="block max-w-xs truncate">{p.direccion}</span>,
      },
      {
        key: "superficie",
        header: "Superficie (m2)",
        align: "right",
        className: "whitespace-nowrap tabular-nums",
        render: (p) => fmtSurface(p.superficie_m2),
      },
      {
        key: "estado",
        header: "Estado",
        render: (p) => {
          const b = esquematicoBadge(p.esquematico_generado);
          return <StatusBadge tone={b.tone}>{b.label}</StatusBadge>;
        },
      },
      {
        key: "fuente",
        header: "Fuente",
        render: (p) => {
          const b = fuenteBadge(p.fuente);
          return <StatusBadge tone={b.tone}>{b.label}</StatusBadge>;
        },
      },
      {
        key: "detalle",
        header: "",
        align: "right",
        className: "w-10 text-slate-300",
        render: () => <ChevronRight size={16} className="ml-auto" aria-hidden="true" />,
      },
    ],
    [],
  );

  return (
    <>
      <PageHeader
        title="Propiedades"
        subtitle="Portfolio completo del relevamiento técnico, con filtros y búsqueda."
      />

      <FilterBar label="Filtros de propiedades" activeCount={activeCount} onClear={clearFilters}>
        <div className="w-full sm:w-72">
          <SearchInput
            id="busqueda-propiedades"
            label="Buscar por código o dirección"
            value={searchInput}
            onChange={setSearchInput}
            placeholder="Buscar por código o dirección…"
          />
        </div>
        <label className="text-xs font-medium text-slate-500">
          Fuente
          <select
            value={fuente}
            onChange={(e) => setFuente(e.target.value)}
            className={`${FILTER_INPUT_CLASS} mt-1 w-full sm:w-44`}
            aria-label="Fuente"
          >
            <option value="">Todas las fuentes</option>
            <option value="carga manual (legacy)">Legacy</option>
            <option value="automatizacion OCR">Automatizado</option>
          </select>
        </label>
        <label className="text-xs font-medium text-slate-500">
          Estado
          <select
            value={estado}
            onChange={(e) => setEstado(e.target.value as EstadoFiltro | "")}
            className={`${FILTER_INPUT_CLASS} mt-1 w-full sm:w-40`}
            aria-label="Estado"
          >
            <option value="">Todos los estados</option>
            <option value="generado">Con esquemático</option>
            <option value="pendiente">Pendiente</option>
          </select>
        </label>
        <label className="text-xs font-medium text-slate-500">
          Superficie mín (m2)
          <input
            type="number"
            min={0}
            value={minStr}
            onChange={(e) => setMinStr(e.target.value)}
            placeholder="mín"
            className={`${FILTER_INPUT_CLASS} mt-1 w-28`}
            aria-label="Superficie mínima en metros cuadrados"
          />
        </label>
        <label className="text-xs font-medium text-slate-500">
          Superficie máx (m2)
          <input
            type="number"
            min={0}
            value={maxStr}
            onChange={(e) => setMaxStr(e.target.value)}
            placeholder="máx"
            className={`${FILTER_INPUT_CLASS} mt-1 w-28`}
            aria-label="Superficie máxima en metros cuadrados"
          />
        </label>
      </FilterBar>

      {result.status === "loading" && <div className="mt-4"><TableSkeleton rows={10} /></div>}

      {result.status === "error" && (
        <div className="mt-4">
          <ErrorState
            title="No pudimos cargar las propiedades"
            description="Ocurrió un problema al comunicarnos con el servidor."
            detail={result.message}
            onRetry={result.retry}
          />
        </div>
      )}

      {result.status === "ready" && result.data && (
        <div className="mt-4">
          <p className="mb-2 text-sm tabular-nums text-slate-500" aria-live="polite">
            {result.data.items.length} {result.data.items.length === 1 ? "propiedad" : "propiedades"}
          </p>
          {result.data.items.length === 0 ? (
            activeCount > 0 ? (
              <EmptyState
                icon={SearchX}
                title="No encontramos propiedades"
                description="Probá cambiar los filtros o realizar otra búsqueda."
                action={
                  <Button variant="secondary" onClick={clearFilters}>
                    Limpiar filtros
                  </Button>
                }
              />
            ) : (
              <EmptyState
                icon={SearchX}
                title="No hay propiedades cargadas"
                description="El portfolio todavía no tiene propiedades procesadas."
                action={
                  <Button variant="secondary" onClick={() => navigate("/")}>
                    Ir al dashboard
                  </Button>
                }
              />
            )
          ) : (
            <DataTable
              columns={columns}
              rows={result.data.items}
              rowKey={(p) => p.codigo}
              ariaLabel="Listado de propiedades. Fila seleccionable para ver el detalle."
              onRowClick={(p) => navigate(`/propiedades/${p.codigo}`)}
            />
          )}
        </div>
      )}
    </>
  );
}