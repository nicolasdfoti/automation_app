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