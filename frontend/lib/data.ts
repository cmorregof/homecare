import { unstable_noStore as noStore } from "next/cache";

import { getModelResults } from "@/lib/api";
import {
  mockAlerts,
  mockModelMetrics,
  mockPatients,
  mockPrediction,
  mockProfiles,
  mockRagDocuments,
  mockReport,
  mockSystemMetrics,
  mockVitals,
} from "@/lib/mock-data";
import { warnDemoData } from "@/lib/demo-mode";
import { isSupabaseConfigured } from "@/lib/supabase";
import { startOfClinicalDay } from "@/lib/utils";
import { createServerSupabaseClient } from "@/lib/supabase-server";
import type {
  AlertRecord,
  ClinicalReport,
  ModelMetric,
  PatientSummary,
  Profile,
  RagDocument,
  RiskLevel,
  RiskPrediction,
  SystemMetrics,
  UserRole,
  VitalSigns,
} from "@/types";

export async function getCurrentProfile(fallbackRole: UserRole = "patient"): Promise<Profile | null> {
  noStore();
  if (!isSupabaseConfigured()) {
    warnDemoData("el perfil del usuario");
    return mockProfiles.find((profile) => profile.role === fallbackRole) ?? mockProfiles[0];
  }
  const supabase = createServerSupabaseClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return null;
  }
  const { data } = await supabase.from("profiles").select("*").eq("id", user.id).single();
  return (data as Profile | null) ?? null;
}

export async function getPatientDashboardData(patientId?: string) {
  noStore();
  if (!isSupabaseConfigured()) {
    warnDemoData("el panel del paciente: perfil, signos vitales, predicción y reporte");
    return {
      profile: mockProfiles[0],
      vitals: mockVitals,
      prediction: mockPrediction,
      report: mockReport,
    };
  }
  const profile = await getCurrentProfile("patient");
  const resolvedPatientId = patientId ?? profile?.id;
  if (!resolvedPatientId) {
    return { profile, vitals: [], prediction: null, report: null };
  }
  const supabase = createServerSupabaseClient();
  const [{ data: vitals }, { data: predictions }, { data: reports }] = await Promise.all([
    supabase
      .from("vital_signs")
      .select("*")
      .eq("patient_id", resolvedPatientId)
      .order("recorded_at", { ascending: false })
      .limit(10),
    supabase
      .from("risk_predictions")
      .select("*")
      .eq("patient_id", resolvedPatientId)
      .order("predicted_at", { ascending: false })
      .limit(1),
    supabase
      .from("clinical_reports")
      .select("*")
      .eq("patient_id", resolvedPatientId)
      .order("generated_at", { ascending: false })
      .limit(1),
  ]);
  return {
    profile,
    vitals: (vitals as VitalSigns[]) ?? [],
    prediction: ((predictions as RiskPrediction[]) ?? [])[0] ?? null,
    report: ((reports as ClinicalReport[]) ?? [])[0] ?? null,
  };
}

/** A measurement together with the risk the model assigned to it. */
export type HistoryRow = VitalSigns & {
  risk_level: RiskLevel | null;
  risk_probability: number | null;
};

/**
 * One page of the patient's own measurements, each carrying its risk level.
 *
 * The risk comes from `risk_predictions.vital_sign_id`, which is the model's
 * verdict on that specific reading — not a value computed here. Deciding a
 * level in the browser would put a second, divergent set of thresholds next to
 * the backend's.
 *
 * This used to page through getPatientDashboardData(), which limits its query
 * to ten rows: the history could never show an eleventh measurement and the
 * pager capped at two pages regardless of how much the patient had recorded.
 * It now counts and ranges over `vital_signs` directly.
 */
export async function getPatientHistory(page = 1, pageSize = 8): Promise<{
  rows: HistoryRow[];
  total: number;
  page: number;
  pageSize: number;
}> {
  noStore();
  const start = (page - 1) * pageSize;

  if (!isSupabaseConfigured()) {
    warnDemoData("el historial de mediciones y su nivel de riesgo");
    const rows = mockVitals.slice(start, start + pageSize).map((vital) => ({
      ...vital,
      risk_level: null,
      risk_probability: null,
    }));
    return { rows, total: mockVitals.length, page, pageSize };
  }

  const profile = await getCurrentProfile("patient");
  if (!profile?.id) {
    return { rows: [], total: 0, page, pageSize };
  }

  const supabase = createServerSupabaseClient();
  const { data, count, error } = await supabase
    .from("vital_signs")
    .select("*", { count: "exact" })
    .eq("patient_id", profile.id)
    .order("recorded_at", { ascending: false })
    .range(start, start + pageSize - 1);

  reportQueryFailure("el historial de mediciones", error);
  const vitals = (data as VitalSigns[] | null) ?? [];
  const risk = await riskByVitalSign(supabase, vitals);

  return {
    rows: vitals.map((vital) => ({
      ...vital,
      risk_level: (vital.id ? risk.get(vital.id)?.level : null) ?? null,
      risk_probability: (vital.id ? risk.get(vital.id)?.probability : null) ?? null,
    })),
    total: count ?? vitals.length,
    page,
    pageSize,
  };
}

/** Looks up the prediction attached to each measurement on the current page. */
async function riskByVitalSign(
  supabase: ReturnType<typeof createServerSupabaseClient>,
  vitals: VitalSigns[],
): Promise<Map<string, { level: RiskLevel; probability: number }>> {
  const ids = vitals.map((vital) => vital.id).filter((id): id is string => Boolean(id));
  const byVitalSign = new Map<string, { level: RiskLevel; probability: number }>();
  if (!ids.length) {
    return byVitalSign;
  }
  const { data, error } = await supabase
    .from("risk_predictions")
    .select("vital_sign_id, risk_level, risk_probability, predicted_at")
    .in("vital_sign_id", ids)
    .order("predicted_at", { ascending: false });
  reportQueryFailure("el nivel de riesgo del historial", error);

  for (const row of (data as RiskPrediction[] | null) ?? []) {
    // Ordered newest first, so the first prediction seen for a measurement is
    // the current one; a re-run of the model leaves the older row in place.
    if (row.vital_sign_id && !byVitalSign.has(row.vital_sign_id)) {
      byVitalSign.set(row.vital_sign_id, {
        level: row.risk_level,
        probability: row.risk_probability,
      });
    }
  }
  return byVitalSign;
}

export async function getIpsDashboardData(filter?: RiskLevel | "all") {
  noStore();
  if (!isSupabaseConfigured()) {
    warnDemoData("el panel de la IPS: pacientes y alertas");
    const patients = applyRiskFilter(mockPatients, filter);
    return { patients, alerts: mockAlerts };
  }
  const supabase = createServerSupabaseClient();
  const { data: alerts } = await supabase
    .from("alerts")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(25);
  warnDemoData("la lista de pacientes de la IPS");
  return {
    patients: applyRiskFilter(mockPatients, filter),
    alerts: ((alerts as AlertRecord[]) ?? []).map((alert) => ({
      ...alert,
      patient_name: mockPatients.find((patient) => patient.id === alert.patient_id)?.full_name,
    })),
  };
}

export async function getPatientDetail(patientId: string) {
  noStore();
  warnDemoData("la identidad del paciente y sus alertas en el detalle");
  const patient = mockPatients.find((item) => item.id === patientId) ?? mockPatients[0];
  const dashboard = await getPatientDashboardData(patient.id);
  if (!dashboard.vitals.length || !dashboard.prediction || !dashboard.report) {
    warnDemoData("signos, predicción o reporte del detalle de paciente (la consulta real vino vacía)");
  }
  return {
    patient,
    vitals: dashboard.vitals.length ? dashboard.vitals : mockVitals,
    prediction: dashboard.prediction ?? mockPrediction,
    report: dashboard.report ?? mockReport,
    alerts: mockAlerts.filter((alert) => alert.patient_id === patient.id),
  };
}

/**
 * Upper bound on the chunk rows pulled to build the RAG document list.
 *
 * `rag_documents` stores one row per chunk, so the list the admin sees is an
 * aggregation this function does in memory. PostgREST caps a request at 1000
 * rows by default; asking for more makes the cap explicit and lets us notice
 * when we hit it instead of silently under-counting chunks.
 */
const RAG_CHUNK_LIMIT = 2000;

export async function getAdminDashboardData(): Promise<{
  metrics: SystemMetrics;
  modelMetrics: ModelMetric[];
  ragDocuments: RagDocument[];
  profiles: Profile[];
}> {
  noStore();
  const modelMetrics = await safeModelMetrics();

  if (!isSupabaseConfigured()) {
    warnDemoData("el panel de administración: métricas, documentos RAG y usuarios");
    return {
      metrics: mockSystemMetrics,
      modelMetrics,
      ragDocuments: mockRagDocuments,
      profiles: mockProfiles,
    };
  }

  const supabase = createServerSupabaseClient();
  const dayStart = startOfClinicalDay();

  const [profilesResult, chunksResult, reportsResult, alertsResult, criticalResult] = await Promise.all([
    supabase
      .from("profiles")
      .select("id, role, full_name, document_id, phone, telegram_chat_id, ips_id, assigned_doctor_id")
      .order("full_name", { ascending: true }),
    // `content` and `embedding` are excluded on purpose: the embedding alone is
    // 1536 floats per chunk, and neither is shown in the list.
    supabase
      .from("rag_documents")
      .select("id, title, source, created_at")
      .order("created_at", { ascending: false })
      .limit(RAG_CHUNK_LIMIT),
    supabase
      .from("clinical_reports")
      .select("id", { count: "exact", head: true })
      .gte("generated_at", dayStart),
    supabase
      .from("alerts")
      .select("id", { count: "exact", head: true })
      .gte("created_at", dayStart),
    supabase
      .from("alerts")
      .select("id", { count: "exact", head: true })
      .gte("created_at", dayStart)
      .eq("risk_level", "critical"),
  ]);

  reportQueryFailure("la lista de usuarios", profilesResult.error);
  reportQueryFailure("los documentos RAG", chunksResult.error);
  reportQueryFailure("el conteo de reportes de hoy", reportsResult.error);
  reportQueryFailure("el conteo de alertas de hoy", alertsResult.error);
  reportQueryFailure("el conteo de alertas críticas", criticalResult.error);

  const profiles = (profilesResult.data as Profile[] | null) ?? [];
  const chunks = (chunksResult.data as RagChunkRow[] | null) ?? [];

  if (chunks.length === RAG_CHUNK_LIMIT) {
    console.warn(
      `[homecare] rag_documents devolvió el máximo de ${RAG_CHUNK_LIMIT} fragmentos. ` +
        `El conteo por documento puede quedarse corto; conviene agregarlo en SQL.`,
    );
  }

  // A row of one means RLS is still scoping the admin to their own profile:
  // profiles_select_admin (backend/db/migrations/20260903_lock_profile_role.sql)
  // has not been applied yet. Without this warning the screen simply looks like
  // a system with a single user.
  if (profiles.length <= 1 && !profilesResult.error) {
    console.warn(
      "[homecare] `profiles` devolvió una fila o ninguna para un administrador. " +
        "Si la base tiene más usuarios, falta aplicar la migración " +
        "backend/db/migrations/20260903_lock_profile_role.sql, que crea la política profiles_select_admin.",
    );
  }

  return {
    metrics: {
      totalPatients: profiles.filter((profile) => profile.role === "patient").length,
      reportsToday: reportsResult.count ?? 0,
      alertsToday: alertsResult.count ?? 0,
      criticalAlerts: criticalResult.count ?? 0,
    },
    modelMetrics,
    ragDocuments: groupRagChunks(chunks),
    profiles,
  };
}

type RagChunkRow = { id: string; title: string; source: string; created_at: string };

/**
 * Collapses chunk rows into one entry per source document.
 *
 * `rag_documents` has no document-level table: a PDF split into forty chunks is
 * forty rows sharing `title` and `source`. Listing them raw showed the same
 * document forty times. Grouping belongs in SQL, but PostgREST cannot GROUP BY
 * without a dedicated RPC, and adding one would change the schema the backend
 * and the Telegram bot already read.
 */
function groupRagChunks(rows: RagChunkRow[]): RagDocument[] {
  const documents = new Map<string, RagDocument>();
  for (const row of rows) {
    const key = `${row.source}\u0000${row.title}`;
    const existing = documents.get(key);
    if (existing) {
      existing.chunk_count += 1;
      // Keep the oldest chunk's timestamp: that is when the document was ingested.
      if (row.created_at < existing.created_at) {
        existing.created_at = row.created_at;
      }
      continue;
    }
    documents.set(key, {
      id: row.id,
      title: row.title,
      source: row.source,
      chunk_count: 1,
      created_at: row.created_at,
    });
  }
  return [...documents.values()].sort((a, b) => b.created_at.localeCompare(a.created_at));
}

/**
 * Reports a failed read without substituting invented data.
 *
 * Falling back to mocks here would be the worst possible behaviour: the screen
 * would look healthy while showing fiction. An empty list or a zero is wrong in
 * a way an administrator can see.
 */
function reportQueryFailure(label: string, error: { message: string } | null) {
  if (!error) {
    return;
  }
  console.error(`[homecare] Falló la consulta de ${label}: ${error.message}`);
}

export async function safeModelMetrics(): Promise<ModelMetric[]> {
  try {
    const response = await getModelResults();
    if (Array.isArray(response.results) && response.results.length) {
      return response.results as ModelMetric[];
    }
  } catch {
    warnDemoData("las métricas de modelos ML (el backend no respondió)");
    return mockModelMetrics;
  }
  warnDemoData("las métricas de modelos ML (el backend respondió sin resultados)");
  return mockModelMetrics;
}

function applyRiskFilter(patients: PatientSummary[], filter?: RiskLevel | "all") {
  const riskRank: Record<RiskLevel, number> = { critical: 4, high: 3, moderate: 2, low: 1 };
  return [...patients]
    .filter((patient) => !filter || filter === "all" || patient.latest_risk === filter)
    .sort((a, b) => riskRank[b.latest_risk] - riskRank[a.latest_risk]);
}
