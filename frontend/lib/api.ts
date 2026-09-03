import type { ModelMetric, RiskLevel, VitalSigns } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Why a request failed, in the terms a person needs to hear.
 *
 * - `unreachable`: the request never got an answer. The backend is down, the
 *   network is out, or NEXT_PUBLIC_API_URL is missing or wrong — that last one
 *   bakes `http://localhost:8000` into the browser bundle, so every patient's
 *   browser politely tries to reach their own machine.
 * - `rejected`: the server answered and refused the data (4xx). Its own
 *   explanation is in `detail`.
 * - `server`: the server answered but broke (5xx). The data was fine.
 *
 * The distinction matters because the advice differs. "Check your connection"
 * is wrong for all three when the real cause is configuration.
 */
export type ApiFailure = "unreachable" | "rejected" | "server";

export class ApiError extends Error {
  readonly failure: ApiFailure;
  readonly status?: number;
  /** The server's own message, when it gave one. */
  readonly detail?: string;

  constructor(failure: ApiFailure, message: string, status?: number, detail?: string) {
    super(message);
    this.name = "ApiError";
    this.failure = failure;
    this.status = status;
    this.detail = detail;
  }
}

/** FastAPI puts its explanation in `detail`, sometimes as a list. */
async function readDetail(response: Response): Promise<string | undefined> {
  try {
    const body = await response.json();
    const detail = body?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      const messages = detail.map((item) => item?.msg).filter(Boolean);
      return messages.length ? messages.join("; ") : undefined;
    }
    if (typeof body?.message === "string") {
      return body.message;
    }
  } catch {
    // A non-JSON body tells us nothing useful; the status already did.
  }
  return undefined;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, init);
  } catch {
    // fetch only rejects when the request never completed: DNS, refused
    // connection, blocked mixed content, CORS preflight, offline.
    throw new ApiError("unreachable", `No hubo respuesta de ${API_URL}${path}.`);
  }

  if (!response.ok) {
    const detail = await readDetail(response);
    const failure: ApiFailure = response.status >= 500 ? "server" : "rejected";
    throw new ApiError(failure, detail ?? `El servidor respondió ${response.status}.`, response.status, detail);
  }

  return response.json() as Promise<T>;
}

export function getHealth() {
  return request<{ status: string; service: string; environment: string }>("/health", {
    cache: "no-store",
  });
}

export function getModelResults() {
  return request<{ best_model?: string; results: ModelMetric[] }>("/models", { cache: "no-store" });
}

export function sendChatMessage(input: { patient_id: string; message: string }) {
  return request<{ reply: string }>("/agents/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function processVitalReport(input: {
  patient_id: string;
  raw_message: string;
  vital_signs?: VitalSigns;
}) {
  return request<{
    risk_level?: RiskLevel;
    risk_probability?: number;
    recommendations?: string;
    follow_up_actions?: string;
    final_response: string;
  }>("/agents/vital-report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      patient_id: input.patient_id,
      raw_message: input.raw_message,
      vital_signs: input.vital_signs ?? {},
      source: "web",
    }),
  });
}
