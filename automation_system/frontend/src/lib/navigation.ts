import type { LucideIcon } from "lucide-react";
import {
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
    title: "Pipeline OCR",
    items: [
      { to: "/esquematicos", label: "Esquemáticos", icon: Files },
      { to: "/ocr", label: "OCR", icon: ScanLine },
      { to: "/comparar", label: "Comparar", icon: GitCompareArrows },
      { to: "/automatizar", label: "Automatizar", icon: Workflow },
    ],
  },
];

export const BRAND = {
  name: "Pipeline OCR",
  caption: "Esquemáticos · Correcciones",
  icon: Files,
  path: "/",
} as const;

const LABELS: Record<string, { label: string; to?: string }> = {
  esquematicos: { label: "Esquemáticos", to: "/esquematicos" },
  ocr: { label: "OCR", to: "/ocr" },
  comparar: { label: "Comparar", to: "/comparar" },
  automatizar: { label: "Automatizar", to: "/automatizar" },
};

export function breadcrumbsFor(pathname: string): { label: string; to?: string }[] {
  const segments = pathname.split("/").filter(Boolean);
  const root = { label: "Pipeline OCR", to: "/esquematicos" };
  if (segments.length === 0) {
    return [{ label: "Esquemáticos", to: "/esquematicos" }];
  }
  const crumbs: { label: string; to?: string }[] = [root];
  segments.forEach((segment, index) => {
    const known = LABELS[segment];
    if (known) {
      crumbs.push({
        label: known.label,
        to: segments.length > index + 1 ? known.to : undefined,
      });
      return;
    }
    crumbs.push({ label: `Propiedad ${segment}`, to: undefined });
  });
  return crumbs;
}