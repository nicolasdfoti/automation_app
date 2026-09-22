import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Loader2 } from "lucide-react";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md";

const BASE =
  "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50 select-none";

const VARIANTS: Record<ButtonVariant, string> = {
  primary: "bg-primary-500 text-white hover:bg-primary-600 active:bg-primary-700",
  secondary: "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 hover:text-slate-900",
  ghost: "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
  danger: "bg-error-600 text-white hover:bg-error-700",
};

const SIZES: Record<ButtonSize, string> = {
  md: "h-9 px-4 text-sm",
  sm: "h-8 px-3 text-xs",
};

export function buttonClass(variant: ButtonVariant = "primary", size: ButtonSize = "md"): string {
  return `${BASE} ${VARIANTS[variant]} ${SIZES[size]}`;
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: ReactNode;
  loading?: boolean;
}

export default function Button({
  variant = "primary",
  size = "md",
  icon,
  loading = false,
  children,
  disabled,
  className,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`${buttonClass(variant, size)} ${className ?? ""}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? <Loader2 className="animate-spin" size={size === "sm" ? 14 : 16} /> : icon}
      {children}
    </button>
  );
}