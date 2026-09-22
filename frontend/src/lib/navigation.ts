import type { LucideIcon } from "lucide-react";
import {
  Boxes,
  Building2,
  Files,
  GitCompareArrows,
  ScanLine,
  Workflow,
} from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  /** Destination that is not implemented yet (clearly marked as such). */
  upcoming?: boolean;
}

export const NAV_SECTIONS: { title: string; items: NavItem[] }[] = [
  {
    title: "Operación",
    items: [
      { to: "/", label: "Dashboard", icon: Boxes },
      { to: "/propiedades", label: "Propiedades", icon: Building2 },
    ],
  },
  {
    title: "Pipeline OCR",
    items: [
      { to: "/esquematicos", label: "Esquemáticos", icon: Files },
      { to: "/ocr", label: "OCR", icon: ScanLine },
      { to: "/comparar", label: "Comparar", icon: GitCompareArrows },
      { to: "/automatizar", label: "Automatizar", icon: Workflow, upcoming: true },
    ],
  },
];

export const BRAND = {
  name: "Automation Suite",
  caption: "Plataforma de operaciones",
  icon: Boxes,
  path: "/",
} as const;

const LABELS: Record<string, { label: string; to?: string }> = {
  "": { label: "Dashboard", to: "/" },
  propiedades: { label: "Propiedades", to: "/propiedades" },
  esquematicos: { label: "Esquemáticos", to: "/esquematicos" },
  ocr: { label: "OCR", to: "/ocr" },
  comparar: { label: "Comparar", to: "/comparar" },
  automatizar: { label: "Automatizar", to: "/automatizar" },
};

export function breadcrumbsFor(pathname: string): { label: string; to?: string }[] {
  if (pathname === "/" || pathname === "") {
    return [{ label: "Dashboard", to: "/" }];
  }
  const segments = pathname.split("/").filter(Boolean);
  const crumbs: { label: string; to?: string }[] = [{ label: "Dashboard", to: "/" }];
  segments.forEach((segment, index) => {
    const known = LABELS[segment];
    if (known) {
      crumbs.push({
        label: known.label,
        to: segments.length > index + 1 ? known.to : undefined,
      });
      return;
    }
    // property code segment: `/propiedades/:codigo`
    crumbs.push({ label: `Propiedad ${segment}`, to: undefined });
  });
  return crumbs;
}