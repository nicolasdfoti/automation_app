import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Download, FileText, MapPin } from "lucide-react";
import { ApiError } from "../api/client";
import { fetchProperty, updateProperty } from "../api/properties";
import { getSchematicDownloadUrl } from "../api/schematics";
import StatusBadge from "../components/ui/StatusBadge";
import SectionCard from "../components/ui/SectionCard";
import ErrorState from "../components/ui/ErrorState";
import Button from "../components/ui/Button";
import Field, { FIELD_INPUT_CLASS } from "../components/ui/Field";
import { DetailSkeleton } from "../components/ui/Skeleton";
import { useApi, esquematicoBadge, fuenteBadge } from "../hooks/useApi";
import type { Property } from "../types";

interface FormValues {
  direccion: string;
  superficie_m2: string;
  capacidad_personas: string;
  plazas_estacionamiento: string;
  anio_construccion: string;
  salas: string;
}

interface SaveFeedback {
  kind: "success" | "error";
  text: string;
}

const EMPTY_FORM: FormValues = {
  direccion: "",
  superficie_m2: "",
  capacidad_personas: "",
  plazas_estacionamiento: "",
  anio_construccion: "",
  salas: "",
};

function errorText(err: unknown): string {
  return err instanceof ApiError ? err.message : "Ocurrió un problema inesperado.";
}

function toForm(p: Property): FormValues {
  return {
    direccion: p.direccion,
    superficie_m2: String(p.superficie_m2),
    capacidad_personas: String(p.capacidad_personas),
    plazas_estacionamiento: String(p.plazas_estacionamiento),
    anio_construccion: String(p.anio_construccion),
    salas: String(p.salas),
  };
}

export default function PropertyDetailPage() {
  const { codigo } = useParams<{ codigo: string }>();
  const result = useApi(() => fetchProperty(codigo ?? ""), [codigo]);
  const [saved, setSaved] = useState<Property | null>(null);
  const [form, setForm] = useState<FormValues>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [saveFeedback, setSaveFeedback] = useState<SaveFeedback | null>(null);

  const property = saved ?? (result.status === "ready" ? result.data : undefined);

  useEffect(() => {
    if (result.data) {
      setForm(toForm(result.data));
      setSaved(null);
      setSaving(false);
      setSaveFeedback(null);
    }
  }, [result.data]);

  const is404 = result.statusCode === 404;

  const isDirty = (() => {
    if (!property) return false;
    return (
      form.direccion !== property.direccion ||
      parseFloat(form.superficie_m2) !== property.superficie_m2 ||
      parseInt(form.capacidad_personas, 10) !== property.capacidad_personas ||
      parseInt(form.plazas_estacionamiento, 10) !== property.plazas_estacionamiento ||
      parseInt(form.anio_construccion, 10) !== property.anio_construccion ||
      parseInt(form.salas, 10) !== property.salas
    );
  })();

  const handleSave = async () => {
    if (!property || saving) return;
    const superficie_m2 = parseFloat(form.superficie_m2);
    const capacidad_personas = parseInt(form.capacidad_personas, 10);
    const plazas_estacionamiento = parseInt(form.plazas_estacionamiento, 10);
    const anio_construccion = parseInt(form.anio_construccion, 10);
    const salas = parseInt(form.salas, 10);

    if (!form.direccion.trim()) {
      setSaveFeedback({ kind: "error", text: "La dirección no puede quedar vacía." });
      return;
    }
    if (!Number.isFinite(superficie_m2) || superficie_m2 <= 0) {
      setSaveFeedback({ kind: "error", text: "La superficie debe ser un número mayor a 0." });
      return;
    }
    if (
      !Number.isFinite(capacidad_personas) ||
      !Number.isFinite(plazas_estacionamiento) ||
      !Number.isFinite(anio_construccion) ||
      !Number.isFinite(salas)
    ) {
      setSaveFeedback({ kind: "error", text: "Todos los campos numéricos deben estar completos." });
      return;
    }

    setSaving(true);
    setSaveFeedback(null);
    try {
      const updated = await updateProperty(property.codigo, {
        direccion: form.direccion.trim(),
        superficie_m2,
        capacidad_personas,
        plazas_estacionamiento,
        anio_construccion,
        salas,
      });
      setSaved(updated);
      setForm(toForm(updated));
      setSaveFeedback({ kind: "success", text: "Cambios guardados correctamente." });
    } catch (err) {
      setSaveFeedback({ kind: "error", text: errorText(err) });
    } finally {
      setSaving(false);
    }
  };

  const handleDiscard = () => {
    if (property) setForm(toForm(property));
    setSaveFeedback(null);
  };

  const setField = (key: keyof FormValues, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setSaveFeedback(null);
  };

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
              description="Datos técnicos del portfolio. Editalos y guardá los cambios."
            >
              <div className="grid grid-cols-1 gap-x-6 gap-y-5 sm:grid-cols-2">
                <Field id="property-field-codigo" label="Código" className="sm:col-span-2">
                  <input
                    id="property-field-codigo"
                    name="codigo"
                    type="text"
                    value={property.codigo}
                    disabled
                    aria-describedby="codigo-hint"
                    className={FIELD_INPUT_CLASS}
                  />
                </Field>
                <p id="codigo-hint" className="sr-only">
                  El código es el identificador de la propiedad y no se puede modificar.
                </p>

                <Field id="property-field-direccion" label="Dirección" className="sm:col-span-2">
                  <input
                    id="property-field-direccion"
                    name="direccion"
                    type="text"
                    value={form.direccion}
                    onChange={(e) => setField("direccion", e.target.value)}
                    autoComplete="off"
                    className={FIELD_INPUT_CLASS}
                  />
                </Field>

                <Field id="property-field-superficie" label="Superficie" suffix="m2">
                  <input
                    id="property-field-superficie"
                    name="superficie_m2"
                    type="number"
                    min={0}
                    step={0.1}
                    value={form.superficie_m2}
                    onChange={(e) => setField("superficie_m2", e.target.value)}
                    className={`${FIELD_INPUT_CLASS} tabular-nums`}
                  />
                </Field>

                <Field id="property-field-capacidad" label="Capacidad" suffix="pers.">
                  <input
                    id="property-field-capacidad"
                    name="capacidad_personas"
                    type="number"
                    min={0}
                    step={1}
                    value={form.capacidad_personas}
                    onChange={(e) => setField("capacidad_personas", e.target.value)}
                    className={`${FIELD_INPUT_CLASS} tabular-nums`}
                  />
                </Field>

                <Field id="property-field-estacionamiento" label="Estacionamiento" suffix="plazas">
                  <input
                    id="property-field-estacionamiento"
                    name="plazas_estacionamiento"
                    type="number"
                    min={0}
                    step={1}
                    value={form.plazas_estacionamiento}
                    onChange={(e) => setField("plazas_estacionamiento", e.target.value)}
                    className={`${FIELD_INPUT_CLASS} tabular-nums`}
                  />
                </Field>

                <Field id="property-field-anio" label="Año de construcción">
                  <input
                    id="property-field-anio"
                    name="anio_construccion"
                    type="number"
                    min={1900}
                    step={1}
                    value={form.anio_construccion}
                    onChange={(e) => setField("anio_construccion", e.target.value)}
                    className={`${FIELD_INPUT_CLASS} tabular-nums`}
                  />
                </Field>

                <Field id="property-field-salas" label="Salas / ambientes" suffix="u.">
                  <input
                    id="property-field-salas"
                    name="salas"
                    type="number"
                    min={0}
                    step={1}
                    value={form.salas}
                    onChange={(e) => setField("salas", e.target.value)}
                    className={`${FIELD_INPUT_CLASS} tabular-nums`}
                  />
                </Field>

                <Field id="property-field-fuente" label="Fuente">
                  <div className="flex h-9 items-center rounded-md border border-slate-200 bg-slate-50 px-1.5">
                    {(() => {
                      const f = fuenteBadge(property.fuente);
                      return <StatusBadge tone={f.tone}>{f.label}</StatusBadge>;
                    })()}
                  </div>
                </Field>

                <Field id="property-field-ultima-actualizacion" label="Última actualización">
                  <div className="flex h-9 items-center rounded-md border border-slate-200 bg-slate-50 px-3 text-sm tabular-nums text-slate-500">
                    {property.ultima_actualizacion}
                  </div>
                </Field>
              </div>

              <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 pt-5">
                <div className="flex min-w-0 items-center gap-3">
                  {isDirty && (
                    <span className="inline-flex items-center rounded-md bg-warning-50 px-2 py-1 text-xs font-medium text-warning-700">
                      Cambios sin guardar
                    </span>
                  )}
                  {saveFeedback && (
                    <div
                      role={saveFeedback.kind === "error" ? "alert" : "status"}
                      className={`text-sm ${saveFeedback.kind === "success" ? "text-success-700" : "text-error-700"}`}
                    >
                      {saveFeedback.text}
                    </div>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  {isDirty && (
                    <Button type="button" variant="ghost" onClick={handleDiscard} disabled={saving}>
                      Descartar
                    </Button>
                  )}
                  <Button onClick={handleSave} loading={saving} disabled={!isDirty || saving}>
                    {saving ? "Guardando…" : "Guardar cambios"}
                  </Button>
                </div>
              </div>
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
                      <a
                        href={getSchematicDownloadUrl(property.codigo)}
                        download
                        className="mt-3 inline-flex h-8 items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 text-xs font-medium text-slate-700 transition-colors duration-150 hover:bg-slate-50 hover:text-slate-900"
                      >
                        <Download size={13} aria-hidden="true" />
                        Descargar PDF
                      </a>
                    </>
                  ) : (
                    <>
                      <p className="text-sm font-medium text-slate-900">Sin esquemático generado</p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        Esta propiedad todavía no tiene plano técnico. Generalo desde la sección
                        Esquemáticos.
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