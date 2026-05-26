export type UserRole = "patient" | "ips" | "admin";
export type RiskLevel = "low" | "moderate" | "high" | "critical";

export interface Profile {
  id: string;
  role: UserRole;
  full_name: string;
  document_id?: string | null;
  phone?: string | null;
  telegram_chat_id?: number | null;
  ips_id?: string | null;
  assigned_doctor_id?: string | null;
  email?: string | null;
}

export interface VitalSigns {
  id?: string;
  patient_id?: string;
  recorded_at?: string;
  source?: "telegram" | "web" | "manual";
  systolic_bp?: number;
  diastolic_bp?: number;
  heart_rate?: number;
  oxygen_saturation?: number;
  temperature?: number;
  glucose?: number;
  weight_kg?: number;
  pain_score?: number;
  dizziness_score?: number;
  dyspnea_score?: number;
  raw_message?: string;
  notes?: string;
}

export interface RiskPrediction {
  id: string;
  patient_id: string;
  vital_sign_id?: string | null;
  predicted_at: string;
  risk_level: RiskLevel;
  risk_probability: number;
  probabilities?: Record<RiskLevel, number>;
  model_used: string;
  top_risk_factors?: Array<{ feature: string; value?: unknown; shap?: number; points?: number; reason?: string }>;
  confidence_score?: number | null;
}

export interface ClinicalReport {
  id: string;
  patient_id: string;
  vital_sign_id?: string | null;
  prediction_id?: string | null;
  generated_at: string;
  interpretation: string;
  recommendations: string;
  follow_up_actions?: string | null;
  rag_sources?: Array<{ title?: string; source?: string }>;
}

export interface AlertRecord {
  id: string;
  patient_id: string;
  patient_name?: string;
  created_at: string;
  risk_level: RiskLevel;
  message: string;
  acknowledged: boolean;
  sent_to_patient?: boolean;
  sent_to_doctor?: boolean;
  email_sent?: boolean;
  telegram_sent?: boolean;
}

export interface PatientSummary {
  id: string;
  full_name: string;
  document_id?: string | null;
  age?: number | null;
  city?: string | null;
  department?: string | null;
  latest_risk: RiskLevel;
  latest_probability: number;
  latest_vitals?: VitalSigns;
  trend: RiskLevel[];
  last_report_at: string;
  assigned_doctor?: string;
}

export interface ModelMetric {
  model: string;
  status: string;
  train_rows_used?: number;
  validation?: {
    f1_macro?: number;
    accuracy?: number;
    roc_auc_ovr?: number | null;
  };
  test?: {
    f1_macro?: number;
    accuracy?: number;
    roc_auc_ovr?: number | null;
  };
}

export interface RagDocument {
  id: string;
  title: string;
  source: string;
  chunk_count: number;
  created_at: string;
}

export interface SystemMetrics {
  totalPatients: number;
  reportsToday: number;
  alertsToday: number;
  criticalAlerts: number;
}
