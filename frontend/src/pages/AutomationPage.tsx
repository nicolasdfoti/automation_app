import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  CheckCircle2,
  ClipboardCheck,
  ScanLine,
  Sparkles,
  Workflow,
} from "lucide-react";
import { ApiError } from "../api/client";
import { applyAutomation, fetchAutomationPreview } from "../api/automation";
import { fetchOcrStatus } from "../api/ocr";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import StatCard from "../components/ui/StatCard";
import Button from "../components/ui/Button";
import Dialog from "../components/ui/Dialog";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import DataTable, { type DataColumn } from "../components/ui/DataTable";
import { KPISkeleton, TableSkeleton } from "../components/ui/Skeleton";
import { useApi } from "../hooks/useApi";
import { fmtInt, fmtSurface } from "../lib/format";
import type { AutomationItem, OcrStatus } from "../types";

const CAMPO_META: Record<string, { label: string; unit: string }> = {
  superficie_m2: { label: "Superficie", unit: " m²" },
  capacidad_personas: { label: "Capacidad", unit: " pers." },
  plazas_estacionamiento: { label: "Estacionamiento", unit: " u." },
  anio_construccion: { label: "Año", unit: "" },
  salas: { label: "Salas", unit: " u." },
};

function formatChange(campo: string, value: number | null): string {
  const meta = CAMPO_META[campo] ?? { label: campo, unit: "" };
  if (value == null) return "—";
  const formatted = campo === "superficie_m2" ? fmtSurface(value) : fmtInt(value);
  return `${formatted}${meta.unit}`;
}

function errorText(err: unknown): string {
  return err instanceof ApiError ? err.message : "Ocurrió un problema inesperado.";
}

interface Feedback {
  kind: "success" | "error";
  text: string;
}

function ChangeList({ item }: { item: AutomationItem }) {
  return (
    <div className="min-w-[340px] space-y-1.5">
      {item.changes.map((change) => (
        <div key={change.field} className="flex items-center gap-2 text-xs">
          <span className="w-28 shrink-0 font-medium text-slate-600">
            {CAMPO_META[change.field]?.label ?? change.label}
          </span>
          <span className="text-slate-400">Actual</span>
          <span className="font-mono tabular-nums text-slate-500">
            {formatChange(change.field, change.current_value)}
          </span>
          <span className="text-slate-400">→</span>
          <span className="text-slate-400">Nuevo</span>
          <span className="font-mono tabular-nums font-semibold text-slate-900">
            {formatChange(change.field, change.new_value)}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function AutomationPage() {
  const preview = useApi(fetchAutomationPreview, []);
  const ocr = useApi<OcrStatus>(fetchOcrStatus, []);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [applying, setApplying] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  const data = preview.data;
  const changes = data?.total_changes ?? 0;
  const withChanges = data?.properties_with_changes ?? 0;
  const noChanges = Math.max(0, (data?.total_properties ?? 0) - withChanges);

  const doApply = async () => {
    if (applying) return;
    setConfirmOpen(false);
    setApplying(true);
    setFeedback(null);
    try {
      const result = await applyAutomation();
      const nounProps = result.updated_properties === 1 ? "propiedad" : "propiedades";
      const nounFields = result.updated_fields === 1 ? "campo" : "campos";
      setFeedback({
        kind: "success",
        text: `Correcciones aplicadas correctamente — ${result.updated_properties} ${nounProps} actualizadas, ${result.updated_fields} ${nounFields} actualizados.`,
      });
      preview.retry();
    } catch (err) {
      setFeedback({ kind: "error", text: `No se pudieron aplicar las correcciones. ${errorText(err)}` });
    } finally {
      setApplying(false);
    }
  };

  const ocrNotRun = ocr.status === "ready" && (ocr.data?.procesados ?? 0) === 0;

  const columns: DataColumn<AutomationItem>[] = [
    {
      key: "codigo",
      header: "Código",
      className: "whitespace-nowrap font-mono font-medium text-slate-900",
      render: (item) => item.codigo,
    },
    {
      key: "direccion",
      header: "Dirección",
      render: (item) => <span className="block max-w-[240px] truncate text-slate-600">{item.direccion ?? "—"}</span>,
    },
    {
      key: "cambios",
      header: "Cambios propuestos",
      render: (item) => <ChangeList item={item} />,
    },
    {
      key: "accion",
      header: "Acción",
      align: "right",
      className: "w-36",
      render: (item) => (
        <Link
          to={`/propiedades/${item.codigo}`}
          className="inline-flex h-8 items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 text-xs font-medium text-slate-700 transition-colors duration-150 hover:bg-slate-50 hover:text-slate-900"
        >
          Ver propiedad
          <ArrowRight size={13} aria-hidden="true" />
        </Link>
      ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Automatizar"
        subtitle="Revisá las diferencias detectadas por el OCR contra los datos actuales y aplicalas al sistema de propiedades."
        actions={
          <Button
            icon={<Sparkles size={16} aria-hidden="true" />}
            disabled={withChanges === 0 || applying || preview.status === "loading"}
            loading={applying}
            onClick={() => setConfirmOpen(true)}
          >
            {applying ? "Aplicando…" : "Aplicar correcciones"}
          </Button>
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

      {preview.status === "loading" && (
        <div className="space-y-6">
          <KPISkeleton count={3} />
          <TableSkeleton rows={10} columns={4} />
        </div>
      )}

      {preview.status === "error" && (
        <ErrorState
          title="No pudimos calcular las correcciones"
          description="Ocurrió un problema al comunicarnos con el servidor."
          detail={preview.message}
          onRetry={preview.retry}
        />
      )}

      {preview.status === "ready" && data && (
        <>
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard icon={ClipboardCheck} label="Propiedades con cambios" value={String(withChanges)} tone="warning" />
            <StatCard icon={Workflow} label="Campos a actualizar" value={String(changes)} hint="según el OCR" tone="primary" />
            <StatCard icon={CheckCircle2} label="Sin cambios" value={String(noChanges)} hint="ya al día" tone="success" />
          </div>

          <SectionCard
            title="Previsualización de correcciones"
            description="Los valores del OCR serán aplicados sobre los datos actuales (stale)."
          >
            {withChanges === 0 ? (
              ocrNotRun ? (
                <EmptyState
                  icon={ScanLine}
                  title="Todavía no hay resultados de OCR"
                  description="Primero generá los esquemáticos y corré el OCR para poder detectar correcciones."
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
                <EmptyState
                  icon={CheckCircle2}
                  title="Todo está actualizado"
                  description="No se detectaron correcciones pendientes."
                />
              )
            ) : (
              <DataTable
                columns={columns}
                rows={data.items}
                rowKey={(item) => item.codigo}
                ariaLabel="Correcciones propuestas por propiedad"
              />
            )}
          </SectionCard>
        </>
      )}

      <Dialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        title="Aplicar correcciones"
        description="Esta acción modificará properties_db.xlsx."
      >
        <p className="text-sm text-slate-600">
          Se actualizarán <strong className="text-slate-900">{withChanges} propiedades</strong> y{" "}
          <strong className="text-slate-900">{changes} campos</strong> en el sistema.
        </p>
        <p className="mt-2 text-sm text-slate-500">
          Los valores del OCR reemplazarán los datos actuales de cada campo detectado. El ground truth y la salida del
          OCR no se modifican.
        </p>
        <div className="mt-5 flex items-center justify-end gap-3">
          <Button variant="ghost" onClick={() => setConfirmOpen(false)} disabled={applying}>
            Cancelar
          </Button>
          <Button onClick={() => void doApply()} loading={applying}>
            {applying ? "Aplicando…" : "Aplicar correcciones"}
          </Button>
        </div>
      </Dialog>
    </>
  );
}