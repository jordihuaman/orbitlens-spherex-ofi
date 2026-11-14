import type {
  Job,
  Manifest,
  Preset,
  SearchPayload,
  SearchStart,
} from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = `Error HTTP ${response.status}`;
    try {
      const body = (await response.json()) as {
        detail?: string | Array<{ msg?: string }>;
      };
      if (typeof body.detail === "string") {
        detail = body.detail;
      } else if (Array.isArray(body.detail)) {
        detail = body.detail
          .map((item) => item.msg ?? "entrada inválida")
          .join("; ");
      }
    } catch {
      // Respuesta sin JSON: se conserva el mensaje HTTP.
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export async function fetchPresets(): Promise<Preset[]> {
  const data = await request<{ presets: Preset[] }>("/api/presets");
  return data.presets;
}

export async function startSearch(payload: SearchPayload): Promise<SearchStart> {
  return request<SearchStart>("/api/search", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchStatus(jobId: string): Promise<Job> {
  return request<Job>(`/api/status/${encodeURIComponent(jobId)}`);
}

export async function fetchManifest(resultId: string): Promise<Manifest> {
  return request<Manifest>(
    `/api/results/${encodeURIComponent(resultId)}/manifest`,
  );
}

export function fileUrl(resultId: string, fileId: string): string {
  return `${API_BASE}/api/results/${encodeURIComponent(
    resultId,
  )}/files/${encodeURIComponent(fileId)}`;
}

export function manifestUrl(resultId: string): string {
  return `${API_BASE}/api/results/${encodeURIComponent(resultId)}/manifest`;
}
