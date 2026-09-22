import { apiFetch } from "./client";
import type { OcrResultList, OcrRunResult, OcrStatus } from "../types";

export function runOcr(reprocesarTodo = false): Promise<OcrRunResult> {
  const query = reprocesarTodo ? "?reprocesar_todo=true" : "";
  return apiFetch<OcrRunResult>(`/api/ocr/run${query}`, { method: "POST" });
}

export function fetchOcrStatus(): Promise<OcrStatus> {
  return apiFetch<OcrStatus>("/api/ocr/status");
}

export function fetchOcrResults(): Promise<OcrResultList> {
  return apiFetch<OcrResultList>("/api/ocr/results");
}