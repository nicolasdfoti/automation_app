export type BadgeTone = "success" | "warning" | "error" | "neutral" | "info";

export interface SchematicCatalogItem {
  codigo: string;
  direccion: string | null;
  superficie_m2: number | null;
  esquematico_generado: boolean;
  archivo_esquematico: string | null;
}

export interface SchematicCatalog {
  count: number;
  items: SchematicCatalogItem[];
}

export interface PendingSchematic {
  codigo: string;
  direccion: string | null;
  superficie_m2: number | null;
  estado: "pendiente";
}

export interface PendingSchematicList {
  count: number;
  items: PendingSchematic[];
}

export interface SchematicResult {
  codigo: string;
  archivo: string | null;
  direccion: string | null;
  fecha_relevamiento: string | null;
  generado: boolean;
  descargable: boolean;
  error: string | null;
}

export interface GenerateAllResult {
  total: number;
  generated: number;
  failed: number;
  results: SchematicResult[];
}

export interface PropertyUpdateInput {
  direccion?: string;
  superficie_m2?: number;
  capacidad_personas?: number;
  plazas_estacionamiento?: number;
  anio_construccion?: number;
  salas?: number;
}

export interface OcrRunResult {
  status: string;
  processed: number;
  total: number;
}

export type OcrEstado = "sin_esquematicos" | "nunca_ejecutado" | "completado";

export interface OcrStatus {
  estado: OcrEstado;
  total_esquematicos: number;
  procesados: number;
  pendientes: number;
}

export interface OcrResultItem {
  codigo: string;
  archivo: string | null;
  direccion: string | null;
  fecha_relevamiento: string | null;
  superficie_m2: number | null;
  capacidad_personas: number | null;
  plazas_estacionamiento: number | null;
  anio_construccion: number | null;
  salas: number | null;
  error: string | null;
}

export interface OcrResultList {
  count: number;
  items: OcrResultItem[];
}

export type CompareStatus = "coincide" | "diferencia" | "sin_datos";

export interface CompareField {
  campo: string;
  coinciden: boolean | null;
  ground_truth: number | null;
  ocr: number | null;
}

export interface CompareItem {
  codigo: string;
  status: CompareStatus;
  todas_correctas: boolean;
  fields: CompareField[];
}

export interface ComparePerField {
  campo: string;
  exactitud: number;
}

export interface CompareResponse {
  total: number;
  coinciden: number;
  diferencias: number;
  sin_datos: number;
  exactitud_global: number;
  propiedades_con_error: number;
  per_field: ComparePerField[];
  items: CompareItem[];
}

export interface AutomationChange {
  field: string;
  label: string;
  current_value: number | null;
  new_value: number | null;
}

export interface AutomationItem {
  codigo: string;
  direccion: string | null;
  changes: AutomationChange[];
}

export interface AutomationPreview {
  total_properties: number;
  properties_with_changes: number;
  total_changes: number;
  items: AutomationItem[];
}

export interface AutomationUpdatedItem {
  codigo: string;
  updated_fields: string[];
}

export interface AutomationApplyResult {
  updated_properties: number;
  updated_fields: number;
  items: AutomationUpdatedItem[];
}