import { apiFetch } from "./client";
import type { CompareResponse } from "../types";

export function fetchCompare(): Promise<CompareResponse> {
  return apiFetch<CompareResponse>("/api/compare");
}