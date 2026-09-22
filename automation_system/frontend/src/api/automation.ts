import { apiFetch } from "./client";
import type { AutomationPreview, PlaywrightAutomationResult } from "../types";

export function fetchAutomationPreview(): Promise<AutomationPreview> {
  return apiFetch<AutomationPreview>("/api/automation/preview");
}

export function automateWithPlaywright(
  codigo: string,
  field?: string,
): Promise<PlaywrightAutomationResult> {
  return apiFetch<PlaywrightAutomationResult>("/api/automation/playwright", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ codigo, field: field ?? null }),
  });
}