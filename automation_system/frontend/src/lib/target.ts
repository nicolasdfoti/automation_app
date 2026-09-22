export const TARGET_UI_URL =
  import.meta.env.VITE_TARGET_UI_URL ?? "http://127.0.0.1:5173";

export function propertyUrlInTarget(codigo: string): string {
  return `${TARGET_UI_URL}/propiedades/${encodeURIComponent(codigo)}`;
}