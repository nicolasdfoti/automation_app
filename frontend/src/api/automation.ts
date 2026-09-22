import { apiFetch } from "./client";
import type { AutomationApplyResult, AutomationPreview } from "../types";

export function fetchAutomationPreview(): Promise<AutomationPreview> {
  return apiFetch<AutomationPreview>("/api/automation/preview");
}

export function applyAutomation(): Promise<AutomationApplyResult> {
  return apiFetch<AutomationApplyResult>("/api/automation/apply", { method: "POST" });
}