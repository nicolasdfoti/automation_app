export function fmtInt(value: number): string {
  return new Intl.NumberFormat("es-AR", { maximumFractionDigits: 0 }).format(value);
}

export function fmtSurface(value: number): string {
  return new Intl.NumberFormat("es-AR", {
    maximumFractionDigits: 1,
    minimumFractionDigits: 0,
  }).format(value);
}

export function fmtCapacidad(value: number): string {
  return new Intl.NumberFormat("es-AR", { maximumFractionDigits: 0 }).format(value);
}

export function formatFuente(fuente: string): string {
  if (fuente === "automatizacion OCR") return "Automatizado";
  return "Legacy";
}