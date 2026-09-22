import { useEffect, useState } from "react";
import { fetchStats } from "../api/properties";
import type { Stats } from "../types";
import { fmtCapacidad, fmtInt, fmtSurface } from "../lib/format";

type State =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; stats: Stats };

export default function Dashboard() {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    fetchStats()
      .then((stats) => {
        if (!cancelled) setState({ status: "ready", stats });
      })
      .catch((err: Error) => {
        if (!cancelled) setState({ status: "error", message: err.message });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.status === "loading") return <p>Cargando indicadores…</p>;
  if (state.status === "error") return <p>Error: {state.message}</p>;

  const { stats } = state;
  const cards = [
    { label: "Propiedades totales", value: fmtInt(stats.total) },
    { label: "Pendientes de esquemático", value: fmtInt(stats.pendientes) },
    { label: "Corregidas por automatización", value: fmtInt(stats.corregidas) },
    { label: "Superficie total (m2)", value: fmtSurface(stats.superficie_total) },
  ];

  return (
    <section>
      <h1 className="mb-6 text-2xl font-semibold text-slate-900">Dashboard</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <div key={card.label} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-xs uppercase tracking-wide text-slate-500">{card.label}</p>
            <p className="mt-2 text-3xl font-bold text-slate-900">{card.value}</p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm text-slate-500">Capacidad total: {fmtCapacidad(stats.capacidad_total)} personas</p>
    </section>
  );
}