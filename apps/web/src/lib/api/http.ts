type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
};

export class AnalyzeApiError extends Error {
  code: string;
  details: Record<string, unknown>;

  constructor(code: string, message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.name = "AnalyzeApiError";
    this.code = code;
    this.details = details;
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
  options?: { fallbackOnError?: T },
): Promise<T> {
  const response = await fetch(path, {
    credentials: "include",
    ...init,
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });

  let data: unknown = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    if (options && "fallbackOnError" in options) {
      return options.fallbackOnError as T;
    }
    const err = data as ApiErrorBody | null;
    throw new AnalyzeApiError(
      err?.error?.code || "ANALYSIS_FAILED",
      err?.error?.message || "Request failed.",
      err?.error?.details || {},
    );
  }

  return data as T;
}
