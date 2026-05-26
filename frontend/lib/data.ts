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
import { isSupabaseConfigured } from "@/lib/supabase";
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

export async function getPatientHistory(page = 1, pageSize = 8) {
  const data = await getPatientDashboardData();
  const start = (page - 1) * pageSize;
  return {
    rows: data.vitals.slice(start, start + pageSize),
    total: data.vitals.length,
    page,
    pageSize,
  };
}

export async function getIpsDashboardData(filter?: RiskLevel | "all") {
  noStore();
  if (!isSupabaseConfigured()) {
    const patients = applyRiskFilter(mockPatients, filter);
    return { patients, alerts: mockAlerts };
  }
  const supabase = createServerSupabaseClient();
  const { data: alerts } = await supabase
    .from("alerts")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(25);
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
  const patient = mockPatients.find((item) => item.id === patientId) ?? mockPatients[0];
  const dashboard = await getPatientDashboardData(patient.id);
  return {
    patient,
    vitals: dashboard.vitals.length ? dashboard.vitals : mockVitals,
    prediction: dashboard.prediction ?? mockPrediction,
    report: dashboard.report ?? mockReport,
    alerts: mockAlerts.filter((alert) => alert.patient_id === patient.id),
  };
}

export async function getAdminDashboardData(): Promise<{
  metrics: SystemMetrics;
  modelMetrics: ModelMetric[];
  ragDocuments: RagDocument[];
  profiles: Profile[];
}> {
  noStore();
  const modelMetrics = await safeModelMetrics();
  return {
    metrics: mockSystemMetrics,
    modelMetrics,
    ragDocuments: mockRagDocuments,
    profiles: mockProfiles,
  };
}

export async function safeModelMetrics(): Promise<ModelMetric[]> {
  try {
    const response = await getModelResults();
    if (Array.isArray(response.results) && response.results.length) {
      return response.results as ModelMetric[];
    }
  } catch {
    return mockModelMetrics;
  }
  return mockModelMetrics;
}

function applyRiskFilter(patients: PatientSummary[], filter?: RiskLevel | "all") {
  const riskRank: Record<RiskLevel, number> = { critical: 4, high: 3, moderate: 2, low: 1 };
  return [...patients]
    .filter((patient) => !filter || filter === "all" || patient.latest_risk === filter)
    .sort((a, b) => riskRank[b.latest_risk] - riskRank[a.latest_risk]);
}
