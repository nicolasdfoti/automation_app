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
import { automateWithPlaywright, fetchAutomationPreview, runPlaywrightBatch } from "../api/automation";
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
import StatusBadge from "../components/ui/StatusBadge";
import { useApi } from "../hooks/useApi";
import { fmtInt, fmtSurface } from "../lib/format";
import { propertyUrlInTarget } from "../lib/target";
import type { AutomationItem, OcrStatus, PlaywrightAutomationResult } from "../types";

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

interface ResultRow {
  key: string;
  codigo: string;
  fieldName: string;
  before: number | null;
  expected: number | null;
  after: number | null;
  verified: boolean;
}

function flattenChanges(result: PlaywrightAutomationResult): ResultRow[] {
  if (result.changes.length > 0) {
    return result.changes.map((c) => ({
      key: `${result.codigo}-${c.field}`,
      codigo: result.codigo,
      fieldName: c.field,
      before: c.before,
      expected: c.expected,
      after: c.after,
      verified: c.verified,
    }));
  }
  if (result.field != null) {
    return [
      {
        key: `${result.codigo}-${result.field}`,
        codigo: result.codigo,
        fieldName: result.field,
        before: result.before,
        expected: result.expected,
        after: result.after,
        verified: result.verified,
      },
    ];
  }
  return [];
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
  const [running, setRunning] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [resultRows, setResultRows] = useState<ResultRow[]>([]);

  const data = preview.data;
  const changes = data?.total_changes ?? 0;
  const withChanges = data?.properties_with_changes ?? 0;
  const noChanges = Math.max(0, (data?.total_properties ?? 0) - withChanges);

  const setResultFeedback = (rows: ResultRow[]) => {
    const properties = new Set(rows.map((r) => r.codigo)).size;
    const verified = rows.filter((r) => r.verified).length;
    const failed = rows.length - verified;
    if (rows.length === 0) {
      setFeedback({ kind: "error", text: "No se corrigió ningún campo (sin cambios pendientes)." });
      return;
    }
    setFeedback({
      kind: failed === 0 ? "success" : "error",
      text:
        failed === 0
          ? `Automatización por browser completada — ${verified} campos verificados en ${properties} propiedad${properties === 1 ? "" : "es"}, aplicados sobre la UI real de Target.`
          : `Automatización por browser con ${failed} campo${failed === 1 ? "" : "s"} que no se pudieron verificar.`,
    });
  };

  const runSingle = async (item: AutomationItem) => {
    if (running) return;
    setRunning(true);
    setFeedback(null);
    setResultRows([]);
    try {
      const result = await automateWithPlaywright(item.codigo);
      const rows = flattenChanges(result);
      setResultRows(rows);
      setResultFeedback(rows);
    } catch (err) {
      setFeedback({
        kind: "error",
        text: `No se pudo automatizar ${item.codigo}. ${errorText(err)}`,
      });
    } finally {
      setRunning(false);
      preview.retry();
    }
  };

  const runBulk = async () => {
    if (running) return;
    setConfirmOpen(false);
    setRunning(true);
    setFeedback(null);
    setResultRows([]);
    const items = data?.items ?? [];
    const rows: ResultRow[] = [];
    let errored = 0;
    try {
      // One "run": the backend opens a single Chromium window and reuses it
      // for every correction before closing it at the end.
      const batch = await runPlaywrightBatch(items.map((it) => it.codigo));
      for (const result of batch.results) {
        const noChange = result.stage === "no_change";
        if (!result.success && !noChange) errored += 1;
        rows.push(...flattenChanges(result));
      }
    } catch {
      errored = Math.max(1, items.length);
    }
    setResultRows(rows);
    if (rows.length === 0) {
      setFeedback({
        kind: "error",
        text: errored === 0
          ? "No se corrigió ningún campo (sin cambios pendientes)."
          : `No se pudo completar ninguna automatización (${errored} ejecuciones fallidas).`,
      });
    } else {
      const properties = new Set(rows.map((r) => r.codigo)).size;
      const verified = rows.filter((r) => r.verified).length;
      setFeedback({
        kind: errored === 0 && verified === rows.length ? "success" : "error",
        text: `Automatización por browser — ${verified}/${rows.length} campos verificados en ${properties} propiedad${properties === 1 ? "" : "es"} con una sola ventana de Chromium` +
          (errored > 0 ? `, ${errored} corrección(es) con error.` : " sobre la UI real de Target."),
      });
    }
    setRunning(false);
    preview.retry();
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
      className: "w-48",
      render: (item) => (
        <div className="flex items-center justify-end gap-2">
          <a
            href={propertyUrlInTarget(item.codigo)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex h-8 items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 text-xs font-medium text-slate-700 transition-colors duration-150 hover:bg-slate-50 hover:text-slate-900"
          >
            Ver
            <ArrowRight size={13} aria-hidden="true" />
          </a>
          <Button
            size="sm"
            variant="secondary"
            icon={<Sparkles size={13} aria-hidden="true" />}
            disabled={running}
            onClick={() => void runSingle(item)}
          >
            Automatizar
          </Button>
        </div>
      ),
    },
  ];

  const resultColumns: DataColumn<ResultRow>[] = [
    {
      key: "codigo",
      header: "Código",
      className: "whitespace-nowrap font-mono font-medium text-slate-900",
      render: (r) => r.codigo,
    },
    {
      key: "campo",
      header: "Campo",
      render: (r) => <span className="text-slate-600">{CAMPO_META[r.fieldName]?.label ?? r.fieldName}</span>,
    },
    {
      key: "before",
      header: "Antes",
      render: (r) => <span className="font-mono tabular-nums text-slate-500">{formatChange(r.fieldName, r.before)}</span>,
    },
    {
      key: "expected",
      header: "Esperado",
      render: (r) => <span className="font-mono tabular-nums text-slate-500">{formatChange(r.fieldName, r.expected)}</span>,
    },
    {
      key: "after",
      header: "Después",
      render: (r) => (
        <span className="font-mono tabular-nums font-semibold text-slate-900">{formatChange(r.fieldName, r.after)}</span>
      ),
    },
    {
      key: "estado",
      header: "Estado",
      align: "right",
      render: (r) =>
        r.verified ? (
          <StatusBadge tone="success">Verificado</StatusBadge>
        ) : (
          <StatusBadge tone="error">Diferente</StatusBadge>
        ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Automatizar"
        subtitle="Revisá las diferencias detectadas por el OCR contra los datos actuales. La corrección se aplica por el navegador real de Target (visible), que se abre una sola vez y se reutiliza para toda la corrida: edita y guarda cada propiedad en su UI antes de cerrarse."
        actions={
          <Button
            icon={<Sparkles size={16} aria-hidden="true" />}
            disabled={withChanges === 0 || running || preview.status === "loading"}
            loading={running}
            onClick={() => setConfirmOpen(true)}
          >
            {running ? "Automatizando…" : "Automatizar todas"}
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

      {resultRows.length > 0 && (
        <div className="mb-6">
          <SectionCard
            title="Resultado de la automatización (browser real)"
            description="Cambios aplicados sobre la UI de Target (:5173) y verificados tras recargar el detalle."
          >
            <DataTable
              columns={resultColumns}
              rows={resultRows}
              rowKey={(r) => r.key}
              ariaLabel="Resultado de la automatización por browser"
            />
          </SectionCard>
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
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard icon={ClipboardCheck} label="Propiedades con cambios" value={String(withChanges)} tone="warning" />
            <StatCard icon={Workflow} label="Campos a actualizar" value={String(changes)} hint="según el OCR" tone="primary" />
            <StatCard icon={CheckCircle2} label="Sin cambios" value={String(noChanges)} hint="ya al día" tone="success" />
          </div>

          <SectionCard
            title="Previsualización de correcciones"
            description="Cada corrección se aplicará por el navegador real de Target, no por Excel."
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
        </div>
      )}

      <Dialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        title="Automatizar todas las correcciones"
        description="Se abre el navegador real de Target (http://127.0.0.1:5173) una sola vez y se reutiliza para todas las correcciones de la corrida."
      >
        <p className="text-sm text-slate-600">
          Se corregirán <strong className="text-slate-900">{withChanges} propiedades</strong> y{" "}
          <strong className="text-slate-900">{changes} campos</strong> en una única ventana de Chromium: edición y
          guardado de cada propiedad en la UI de Target, y cierre del navegador al terminar. Podés ver la ventana
          mientras el proceso avanza.
        </p>
        <p className="mt-2 text-sm text-slate-500">
          Los valores los recomputa el backend desde los archivos autoridad: no se confía en el browser y nunca se
          escribe Excel directamente.
        </p>
        <div className="mt-5 flex items-center justify-end gap-3">
          <Button variant="ghost" onClick={() => setConfirmOpen(false)} disabled={running}>
            Cancelar
          </Button>
          <Button onClick={() => void runBulk()} loading={running}>
            {running ? "Automatizando…" : "Abrir y automatizar"}
          </Button>
        </div>
      </Dialog>
    </>
  );
}