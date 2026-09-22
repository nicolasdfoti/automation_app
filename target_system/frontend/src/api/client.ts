export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export { API_BASE };

const DEFAULT_HEADERS: RequestInit = {
  headers: { Accept: "application/json" },
};

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...DEFAULT_HEADERS, ...init });
  } catch {
    throw new ApiError(0, "No pudimos comunicarnos con el servidor. Verificá que la API esté disponible.");
  }

  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const body: unknown = await res.json();
      if (typeof body === "object" && body !== null) {
        const d = (body as { detail?: unknown }).detail;
        if (typeof d === "string") detail = d;
        else if (Array.isArray(d)) {
          detail = d
            .map((item) => (typeof item === "object" && item !== null ? String((item as { msg?: string }).msg ?? "") : String(item)))
            .filter(Boolean)
            .join("; ");
        }
      }
    } catch {
      // fall back to the status-based detail
    }
    throw new ApiError(res.status, detail);
  }

  return res.json() as Promise<T>;
}