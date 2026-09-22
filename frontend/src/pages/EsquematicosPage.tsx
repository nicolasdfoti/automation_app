import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, FileText, Play } from "lucide-react";
import { ApiError } from "../api/client";
import { fetchProperties } from "../api/properties";
import { generateAllSchematics, generateSchematic, getSchematicDownloadUrl } from "../api/schematics";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import DataTable, { type DataColumn } from "../components/ui/DataTable";
import Button from "../components/ui/Button";
import StatusBadge from "../components/ui/StatusBadge";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import Dialog from "../components/ui/Dialog";
import Field, { FIELD_INPUT_CLASS } from "../components/ui/Field";
import { TableSkeleton } from "../components/ui/Skeleton";
import { useApi } from "../hooks/useApi";
import { fmtSurface } from "../lib/format";
import type { Property, SchematicResult } from "../types";

interface Feedback {
  kind: "success" | "error";
  text: string;
}

function errorText(err: unknown): string {
  return err instanceof ApiError ? err.message : "Ocurrió un problema inesperado.";
}

export default function EsquematicosPage() {
  const propertiesApi = useApi(fetchProperties, []);
  const [items, setItems] = useState<Property[] | null>(null);
  const [dialogProperty, setDialogProperty] = useState<Property | null>(null);
  const [generatingCode, setGeneratingCode] = useState<string | null>(null);
  const [bulkRunning, setBulkRunning] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  useEffect(() => {
    if (propertiesApi.data) setItems(propertiesApi.data.items);
  }, [propertiesApi.data]);

  const pending = useMemo(() => (items ?? []).filter((p) => !p.esquematico_generado), [items]);
  const generated = useMemo(
    () => (items ?? []).filter((p) => p.esquematico_generado && p.archivo_esquematico),
    [items],
  );

  const applyResult = (result: SchematicResult) => {
    setItems((prev) => {
      if (!prev) return prev;
      return prev.map((p) =>
        p.codigo === result.codigo
          ? {
              ...p,
              esquematico_generado: result.generado || p.esquematico_generado,
              archivo_esquematico: result.archivo ?? p.archivo_esquematico,
            }
          : p,
      );
    });
  };

  const handleGenerate = async (values: Record<string, number | undefined>) => {
    if (!dialogProperty) return;
    const codigo = dialogProperty.codigo;
    setGeneratingCode(codigo);
    setFeedback(null);
    try {
      const result = await generateSchematic({ codigo, ...values });
      applyResult(result);
      setFeedback({ kind: "success", text: `Esquemático generado para la propiedad ${codigo}.` });
      setDialogProperty(null);
    } catch (err) {
      setFeedback({ kind: "error", text: errorText(err) });
    } finally {
      setGeneratingCode(null);
    }
  };

  const handleGenerateAll = async () => {
    if (bulkRunning || pending.length === 0) return;
    setBulkRunning(true);
    setFeedback(null);
    try {
      const result = await generateAllSchematics();
      result.results.forEach(applyResult);
      const failedCount = result.failed;
      setFeedback(
        failedCount > 0
          ? {
              kind: "error",
              text: `${result.generated} esquemáticos generados, ${failedCount} con error.`,
            }
          : { kind: "success", text: `${result.generated} de ${result.total} esquemáticos generados.` },
      );
    } catch (err) {
      setFeedback({ kind: "error", text: errorText(err) });
    } finally {
      setBulkRunning(false);
    }
  };

  const pendingColumns: DataColumn<Property>[] = useMemo(
    () => [
      { key: "codigo", header: "Código", className: "whitespace-nowrap font-mono font-medium text-slate-900", render: (p) => p.codigo },
      { key: "direccion", header: "Dirección", className: "max-w-xs truncate text-slate-700", render: (p) => <span className="block max-w-xs truncate">{p.direccion}</span> },
      { key: "superficie", header: "Superficie (m2)", align: "right", className: "whitespace-nowrap tabular-nums", render: (p) => fmtSurface(p.superficie_m2) },
      {
        key: "estado",
        header: "Estado",
        render: () => <StatusBadge tone="warning">Pendiente</StatusBadge>,
      },
      {
        key: "accion",
        header: "Acción",
        align: "right",
        className: "w-28",
        render: (p) => (
          <Button
            size="sm"
            onClick={() => setDialogProperty(p)}
            disabled={generatingCode === p.codigo}
            aria-label={`Generar esquemático para ${p.codigo}`}
          >
            Generar
          </Button>
        ),
      },
    ],
    [generatingCode],
  );

  const generatedColumns: DataColumn<Property>[] = useMemo(
    () => [
      { key: "codigo", header: "Código", className: "whitespace-nowrap font-mono font-medium text-slate-900", render: (p) => p.codigo },
      { key: "direccion", header: "Dirección", className: "max-w-xs truncate text-slate-700", render: (p) => <span className="block max-w-xs truncate">{p.direccion}</span> },
      {
        key: "archivo",
        header: "Archivo",
        render: (p) => (
          <span className="inline-flex items-center gap-1.5 font-mono text-slate-700">
            <FileText size={14} className="shrink-0 text-slate-400" aria-hidden="true" />
            {p.archivo_esquematico}
          </span>
        ),
      },
      {
        key: "estado",
        header: "Estado",
        render: () => <StatusBadge tone="success">Con esquemático</StatusBadge>,
      },
      {
        key: "accion",
        header: "Acción",
        align: "right",
        className: "w-32",
        render: (p) => (
          <a
            href={getSchematicDownloadUrl(p.codigo)}
            download
            className="inline-flex h-8 items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 text-xs font-medium text-slate-700 transition-colors duration-150 hover:bg-slate-50 hover:text-slate-900"
          >
            <FileText size={13} aria-hidden="true" />
            Descargar PDF
          </a>
        ),
      },
    ],
    [],
  );

  return (
    <>
      <PageHeader
        title="Esquemáticos"
        subtitle="Generá y administrá los esquemáticos técnicos de las propiedades."
        actions={
          <Button
            onClick={handleGenerateAll}
            disabled={bulkRunning || pending.length === 0}
            loading={bulkRunning}
          >
            {bulkRunning ? "Generando todos…" : "Generar todos"}
          </Button>
        }
      />

      {feedback && (
        <div
          role="status"
          className={`mb-6 rounded-lg border px-4 py-3 text-sm ${
            feedback.kind === "success"
              ? "border-success-50 bg-success-50 text-success-700"
              : "border-error-50 bg-error-50 text-error-700"
          }`}
        >
          {feedback.text}
        </div>
      )}

      {propertiesApi.status === "loading" && <TableSkeleton rows={8} />}

      {propertiesApi.status === "error" && (
        <ErrorState
          title="No pudimos cargar los esquemáticos"
          description="Ocurrió un problema al comunicarnos con el servidor."
          detail={propertiesApi.message}
          onRetry={propertiesApi.retry}
        />
      )}

      {propertiesApi.status === "ready" && (
        <div className="space-y-6">
          <SectionCard
            title="Propiedades pendientes"
            description="Propiedades que todavía no tienen esquemático técnico generado."
          >
            {pending.length === 0 ? (
              <EmptyState
                icon={CheckCircle2}
                title="No hay propiedades pendientes"
                description="Todas las propiedades del portfolio ya tienen esquemático generado."
              />
            ) : (
              <DataTable
                columns={pendingColumns}
                rows={pending}
                rowKey={(p) => p.codigo}
                ariaLabel="Listado de propiedades pendientes de esquemático"
              />
            )}
          </SectionCard>

          <SectionCard
            title="Esquemáticos generados"
            description="PDFs generados, disponibles para descarga."
          >
            {generated.length === 0 ? (
              <EmptyState
                icon={FileText}
                title="Todavía no se generó ningún esquemático"
                description="Los PDFs generados aparecerán acá para su descarga."
              />
            ) : (
              <DataTable
                columns={generatedColumns}
                rows={generated}
                rowKey={(p) => p.codigo}
                ariaLabel="Listado de esquemáticos generados"
              />
            )}
          </SectionCard>
        </div>
      )}

      <GenerateDialog
        property={dialogProperty}
        busy={generatingCode !== null}
        onCancel={() => setDialogProperty(null)}
        onSubmit={handleGenerate}
      />
    </>
  );
}

interface GenerateDialogProps {
  property: Property | null;
  busy: boolean;
  onCancel: () => void;
  onSubmit: (values: Record<string, number | undefined>) => Promise<void>;
}

function GenerateDialog({ property, busy, onCancel, onSubmit }: GenerateDialogProps) {
  const [superficie, setSuperficie] = useState("");
  const [capacidad, setCapacidad] = useState("");
  const [plazas, setPlazas] = useState("");
  const [anio, setAnio] = useState("");
  const [salas, setSalas] = useState("");

  useEffect(() => {
    if (property) {
      setSuperficie("");
      setCapacidad("");
      setPlazas("");
      setAnio("");
      setSalas("");
    }
  }, [property]);

  const toNumber = (value: string): number | undefined => {
    const trimmed = value.trim();
    if (trimmed === "") return undefined;
    const n = Number(trimmed);
    return Number.isFinite(n) ? n : undefined;
  };

  return (
    <Dialog
      open={property !== null}
      onClose={onCancel}
      title="Generar esquemático"
      description="Los valores se utilizan para dibujar el documento técnico."
    >
      {property && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!busy) {
              onSubmit({
                superficie_m2: toNumber(superficie),
                capacidad_personas: toNumber(capacidad),
                plazas_estacionamiento: toNumber(plazas),
                anio_construccion: toNumber(anio),
                salas: toNumber(salas),
              });
            }
          }}
        >
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
            <p className="font-mono text-sm font-medium text-slate-900">{property.codigo}</p>
            <p className="mt-0.5 text-sm text-slate-500">{property.direccion}</p>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field id="gen-superficie" label="Superficie" suffix="m2">
              <input
                id="gen-superficie"
                name="superficie_m2"
                type="number"
                min={0}
                step={0.1}
                value={superficie}
                onChange={(e) => setSuperficie(e.target.value)}
                placeholder="automático"
                className={FIELD_INPUT_CLASS}
              />
            </Field>
            <Field id="gen-capacidad" label="Capacidad" suffix="pers.">
              <input
                id="gen-capacidad"
                name="capacidad_personas"
                type="number"
                min={0}
                step={1}
                value={capacidad}
                onChange={(e) => setCapacidad(e.target.value)}
                placeholder="automático"
                className={FIELD_INPUT_CLASS}
              />
            </Field>
            <Field id="gen-estacionamiento" label="Estacionamiento" suffix="plazas">
              <input
                id="gen-estacionamiento"
                name="plazas_estacionamiento"
                type="number"
                min={0}
                step={1}
                value={plazas}
                onChange={(e) => setPlazas(e.target.value)}
                placeholder="automático"
                className={FIELD_INPUT_CLASS}
              />
            </Field>
            <Field id="gen-anio" label="Año de construcción">
              <input
                id="gen-anio"
                name="anio_construccion"
                type="number"
                min={0}
                step={1}
                value={anio}
                onChange={(e) => setAnio(e.target.value)}
                placeholder="automático"
                className={FIELD_INPUT_CLASS}
              />
            </Field>
            <Field id="gen-salas" label="Salas / ambientes" suffix="u." className="sm:col-span-2">
              <input
                id="gen-salas"
                name="salas"
                type="number"
                min={0}
                step={1}
                value={salas}
                onChange={(e) => setSalas(e.target.value)}
                placeholder="automático"
                className={`${FIELD_INPUT_CLASS} sm:max-w-[50%]`}
              />
            </Field>
          </div>

          <p className="mt-4 text-xs text-slate-500">
            Dejá los campos en blanco (o 0) para que el valor se derive automáticamente de los
            datos actuales de la propiedad, como en el relevamiento original.
          </p>

          <div className="mt-5 flex items-center justify-end gap-3">
            <Button type="button" variant="ghost" onClick={onCancel} disabled={busy}>
              Cancelar
            </Button>
            <Button type="submit" loading={busy}>
              {busy ? "Generando…" : <><Play size={14} aria-hidden="true" />Generar</>}
            </Button>
          </div>
        </form>
      )}
    </Dialog>
  );
}