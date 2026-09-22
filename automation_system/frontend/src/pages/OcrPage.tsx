import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Clock, Files, Play } from "lucide-react";
import { ApiError } from "../api/client";
import { fetchOcrResults, fetchOcrStatus, runOcr } from "../api/ocr";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import StatCard from "../components/ui/StatCard";
import Button from "../components/ui/Button";
import StatusBadge from "../components/ui/StatusBadge";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import DataTable, { type DataColumn } from "../components/ui/DataTable";
import { TableSkeleton } from "../components/ui/Skeleton";
import { fmtInt, fmtSurface } from "../lib/format";
import type { OcrResultItem, OcrStatus } from "../types";

function errorText(err: unknown): string {
  return err instanceof ApiError ? err.message : "Ocurrió un problema inesperado.";
}

interface Feedback {
  kind: "success" | "error";
  text: string;
}

export default function OcrPage() {
  const [status, setStatus] = useState<OcrStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [results, setResults] = useState<OcrResultItem[] | null>(null);
  const [resultsError, setResultsError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      setStatus(await fetchOcrStatus());
      setStatusError(null);
    } catch (err) {
      setStatusError(errorText(err));
    }
    try {
      const res = await fetchOcrResults();
      setResults(res.items);
      setResultsError(null);
    } catch (err) {
      setResultsError(errorText(err));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const doRun = async (reprocesarTodo: boolean) => {
    if (running) return;
    setRunning(true);
    setFeedback(null);
    try {
      const res = await runOcr(reprocesarTodo);
      const noun = res.processed === 1 ? "propiedad procesada" : "propiedades procesadas";
      setFeedback({ kind: "success", text: `OCR completado — ${res.processed} ${noun}.` });
      await loadAll();
    } catch (err) {
      setFeedback({ kind: "error", text: `No se pudo ejecutar el OCR. ${errorText(err)}` });
    } finally {
      setRunning(false);
    }
  };

  const hasResults = (results?.length ?? 0) > 0;
  const pageDown = statusError !== null && resultsError !== null;
  const hasRun = status?.estado === "completado" && (status.procesados ?? 0) > 0;

  const columns: DataColumn<OcrResultItem>[] = [
    { key: "codigo", header: "Código", className: "whitespace-nowrap font-mono font-medium text-slate-900", render: (r) => r.codigo },
    { key: "archivo", header: "Archivo", className: "whitespace-nowrap font-mono text-slate-700", render: (r) => r.archivo ?? "—" },
    { key: "direccion", header: "Dirección", render: (r) => <span className="block max-w-xs truncate">{r.direccion ?? "—"}</span> },
    { key: "fecha", header: "Fecha", className: "whitespace-nowrap tabular-nums", render: (r) => r.fecha_relevamiento ?? "—" },
    { key: "superficie", header: "Superficie (m2)", align: "right", className: "whitespace-nowrap tabular-nums", render: (r) => (r.superficie_m2 != null ? fmtSurface(r.superficie_m2) : "—") },
    { key: "capacidad", header: "Capacidad", align: "right", className: "whitespace-nowrap tabular-nums", render: (r) => (r.capacidad_personas != null ? fmtInt(r.capacidad_personas) : "—") },
    { key: "estacionamiento", header: "Estacion.", align: "right", className: "whitespace-nowrap tabular-nums", render: (r) => (r.plazas_estacionamiento != null ? fmtInt(r.plazas_estacionamiento) : "—") },
    { key: "anio", header: "Año", align: "right", className: "whitespace-nowrap tabular-nums", render: (r) => (r.anio_construccion != null ? fmtInt(r.anio_construccion) : "—") },
    { key: "salas", header: "Salas", align: "right", className: "whitespace-nowrap tabular-nums", render: (r) => (r.salas != null ? fmtInt(r.salas) : "—") },
    {
      key: "estado",
      header: "Estado",
      render: (r) => (r.error ? <StatusBadge tone="error">Error</StatusBadge> : <StatusBadge tone="success">Procesado</StatusBadge>),
    },
  ];

  return (
    <>
      <PageHeader
        title="Correr OCR"
        subtitle="Procesá los esquemáticos y obtené los datos detectados automáticamente."
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={() => void doRun(false)} disabled={running || loading} loading={running}>
              {running ? "Procesando OCR…" : "Ejecutar OCR"}
            </Button>
            <Button variant="ghost" onClick={() => void doRun(true)} disabled={running || loading}>
              Reprocesar todo
            </Button>
          </div>
        }
      />

      {feedback && (
        <div
          role={feedback.kind === "error" ? "alert" : "status"}
          className={`mb-6 flex items-start gap-3 rounded-lg border px-4 py-3 text-sm ${
            feedback.kind === "success"
              ? "border-success-50 bg-success-50 text-success-700"
              : "border-error-50 bg-error-50 text-error-700"
          }`}
        >
          {feedback.kind === "success" ? <CheckCircle2 size={16} className="mt-0.5 shrink-0" aria-hidden="true" /> : null}
          <span>{feedback.text}</span>
        </div>
      )}

      {pageDown && (
        <ErrorState
          title="No pudimos cargar el estado del OCR"
          description="Ocurrió un problema al comunicarnos con el servidor."
          detail={statusError ?? resultsError ?? ""}
          onRetry={() => void loadAll()}
        />
      )}

      {!pageDown && loading && status === null && results === null && <TableSkeleton rows={6} columns={4} />}

      {!pageDown && !(loading && status === null && results === null) && (
        <>
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard icon={Files} label="Esquemáticos" value={status ? String(status.total_esquematicos) : "—"} hint="PDFs disponibles en shared_store" tone="info" />
            <StatCard icon={CheckCircle2} label="Procesados" value={status ? String(status.procesados) : "—"} hint="con fila en ocr_output.xlsx" tone="success" />
            <StatCard icon={Clock} label="Pendientes" value={status ? String(status.pendientes) : "—"} hint="esperando OCR" tone="warning" />
          </div>

          {resultsError !== null && statusError === null && (
            <div className="mb-6 rounded-lg border border-error-50 bg-error-50 px-4 py-3 text-sm text-error-700" role="alert">
              No pudimos cargar los resultados del OCR. {resultsError}
            </div>
          )}

          <SectionCard title="Resultados OCR" description="Lo que el pipeline detectó en cada esquemático.">
            {!hasResults ? (
              <EmptyState
                icon={Play}
                title={running ? "Procesando OCR…" : "Listo para ejecutar OCR"}
                description="El proceso analizará los esquemáticos disponibles y actualizará los resultados OCR."
                action={
                  !running ? (
                    <Button onClick={() => void doRun(false)} disabled={running}>
                      Ejecutar OCR
                    </Button>
                  ) : undefined
                }
              />
            ) : (
              <DataTable columns={columns} rows={results ?? []} rowKey={(r) => r.codigo} ariaLabel="Resultados de OCR por propiedad" />
            )}
          </SectionCard>

          {hasRun && (
            <p className="mt-4 text-xs text-slate-500">
              {status?.procesados} de {status?.total_esquematicos} esquemáticos procesados hasta ahora.
            </p>
          )}
        </>
      )}
    </>
  );
}