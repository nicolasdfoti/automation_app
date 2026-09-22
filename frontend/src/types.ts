export interface Property {
  codigo: string;
  direccion: string;
  superficie_m2: number;
  capacidad_personas: number;
  plazas_estacionamiento: number;
  anio_construccion: number;
  salas: number;
  esquematico_generado: boolean;
  archivo_esquematico: string | null;
  fuente: string;
  ultima_actualizacion: string;
}

export interface PropertyList {
  count: number;
  items: Property[];
}

export interface Stats {
  total: number;
  pendientes: number;
  corregidas: number;
  superficie_total: number;
  capacidad_total: number;
}

export const FUENTES = ["carga manual (legacy)", "automatizacion OCR"] as const;

export type EstadoFiltro = "generado" | "pendiente";

export type BadgeTone = "success" | "warning" | "error" | "neutral" | "info";

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