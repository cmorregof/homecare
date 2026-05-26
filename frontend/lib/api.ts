const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getHealth() {
  const response = await fetch(`${API_URL}/health`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("No fue posible consultar el backend.");
  }
  return response.json() as Promise<{ status: string; service: string; environment: string }>;
}
