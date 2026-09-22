import { apiFetch } from "./client";
import type { Property, PropertyList, PropertyUpdateInput } from "../types";

export interface PropertiesQuery {
  search?: string;
  fuente?: string;
  estado?: string;
  superficie_min?: number;
  superficie_max?: number;
}

export function fetchProperties(query: PropertiesQuery = {}): Promise<PropertyList> {
  const params = new URLSearchParams();
  if (query.search) params.set("search", query.search);
  if (query.fuente) params.set("fuente", query.fuente);
  if (query.estado) params.set("estado", query.estado);
  if (query.superficie_min != null) params.set("superficie_min", String(query.superficie_min));
  if (query.superficie_max != null) params.set("superficie_max", String(query.superficie_max));

  const qs = params.toString();
  return apiFetch<PropertyList>(`/api/properties${qs ? `?${qs}` : ""}`);
}

export function fetchProperty(codigo: string): Promise<Property> {
  return apiFetch<Property>(`/api/properties/${encodeURIComponent(codigo)}`);
}

export function updateProperty(codigo: string, data: PropertyUpdateInput): Promise<Property> {
  return apiFetch<Property>(`/api/properties/${encodeURIComponent(codigo)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}