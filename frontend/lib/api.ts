import type { ModelMetric, RiskLevel, VitalSigns } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getHealth() {
  const response = await fetch(`${API_URL}/health`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("No fue posible consultar el backend.");
  }
  return response.json() as Promise<{ status: string; service: string; environment: string }>;
}

export async function getModelResults() {
  const response = await fetch(`${API_URL}/models`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("No fue posible consultar las metricas de modelos.");
  }
  return response.json() as Promise<{ best_model?: string; results: ModelMetric[] }>;
}

export async function processVitalReport(input: {
  patient_id: string;
  raw_message: string;
  vital_signs?: VitalSigns;
}) {
  const response = await fetch(`${API_URL}/agents/vital-report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      patient_id: input.patient_id,
      raw_message: input.raw_message,
      vital_signs: input.vital_signs ?? {},
      source: "web",
    }),
  });
  if (!response.ok) {
    throw new Error("No fue posible procesar el reporte con Carmen.");
  }
  return response.json() as Promise<{
    risk_level?: RiskLevel;
    risk_probability?: number;
    recommendations?: string;
    follow_up_actions?: string;
    final_response: string;
  }>;
}
