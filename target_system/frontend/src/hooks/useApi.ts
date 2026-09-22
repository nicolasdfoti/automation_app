import { useCallback, useEffect, useState } from "react";
import type { DependencyList } from "react";
import type { BadgeTone } from "../types";

export type ApiStatus = { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready" };

export interface UseApiResult<T> {
  status: "loading" | "error" | "ready";
  data: T | undefined;
  message: string | undefined;
  /** HTTP status code when the failure came from an API response. */
  statusCode: number | undefined;
  retry: () => void;
}

export function useApi<T>(fn: () => Promise<T>, deps: DependencyList): UseApiResult<T> {
  const [tick, setTick] = useState(0);
  const [state, setState] = useState<{
    status: "loading" | "error" | "ready";
    data?: T;
    message?: string;
    statusCode?: number;
  }>({ status: "loading" });

  const memoFn = useCallback(fn, deps); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    let cancelled = false;
    setState((prev) => (prev.status === "ready" ? { status: "loading" } : prev));
    memoFn()
      .then((data) => {
        if (!cancelled) setState({ status: "ready", data });
      })
      .catch((err: Error) => {
        if (!cancelled) {
          const code = "status" in err && typeof (err as { status?: unknown }).status === "number"
            ? ((err as { status: number }).status)
            : undefined;
          setState({ status: "error", message: err.message, statusCode: code });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [memoFn, tick]);

  return {
    status: state.status,
    data: state.status === "ready" ? state.data : undefined,
    message: state.status === "error" ? state.message : undefined,
    statusCode: state.status === "error" ? state.statusCode : undefined,
    retry: () => setTick((t) => t + 1),
  };
}

export function esquematicoBadge(generado: boolean): { tone: BadgeTone; label: string } {
  return generado
    ? { tone: "success", label: "Con esquemático" }
    : { tone: "warning", label: "Pendiente" };
}

export function fuenteBadge(fuente: string): { tone: BadgeTone; label: string } {
  return fuente === "automatizacion OCR"
    ? { tone: "success", label: "Automatizado" }
    : { tone: "neutral", label: "Legacy" };
}