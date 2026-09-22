import { apiFetch, API_BASE } from "./client";
import type {
  GenerateAllResult,
  PendingSchematicList,
  PropertyUpdateInput,
  SchematicResult,
} from "../types";

export function fetchPendingSchematics(): Promise<PendingSchematicList> {
  return apiFetch<PendingSchematicList>("/api/schematics/pending");
}

export interface SchematicParams extends PropertyUpdateInput {
  codigo: string;
}

export function generateSchematic(params: SchematicParams): Promise<SchematicResult> {
  return apiFetch<SchematicResult>("/api/schematics/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
}

export function generateAllSchematics(): Promise<GenerateAllResult> {
  return apiFetch<GenerateAllResult>("/api/schematics/generate-all", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export function getSchematicDownloadUrl(codigo: string): string {
  return `${API_BASE}/api/schematics/${encodeURIComponent(codigo)}/download`;
}