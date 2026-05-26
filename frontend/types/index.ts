export type UserRole = "patient" | "ips" | "admin";
export type RiskLevel = "low" | "moderate" | "high" | "critical";

export interface VitalSigns {
  systolic_bp?: number;
  diastolic_bp?: number;
  heart_rate?: number;
  oxygen_saturation?: number;
  glucose?: number;
  pain_score?: number;
  dizziness_score?: number;
  dyspnea_score?: number;
}
