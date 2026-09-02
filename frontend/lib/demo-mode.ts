import { isSupabaseConfigured } from "@/lib/supabase";
import type { UserRole } from "@/types";

/**
 * Which parts of a screen are fed by lib/mock-data.ts rather than by Supabase.
 *
 * There are two separate ways that happens, and only one of them is about
 * configuration:
 *
 * 1. Supabase is not configured. Every read in lib/data.ts short-circuits to
 *    mocks (lib/data.ts:33, :49, :104). A single bad environment variable in
 *    Vercel puts the whole product in this state.
 *
 * 2. Supabase IS configured and some reads are STILL mocked, unconditionally:
 *
 *      lib/data.ts:115   patients        — the IPS patient list is always mock
 *      lib/data.ts:118   patient_name    — alert names resolved against mocks
 *      lib/data.ts:125   patient         — patient detail identity
 *      lib/data.ts:129   vitals          — when the real query comes back empty
 *      lib/data.ts:130   prediction      — idem
 *      lib/data.ts:131   report          — idem
 *      lib/data.ts:132   alerts          — patient alerts are always mock
 *      lib/data.ts:145   metrics         — admin system metrics
 *      lib/data.ts:147   ragDocuments    — admin RAG list
 *      lib/data.ts:148   profiles        — admin user list
 *
 * Case 2 is the dangerous one: nothing about the environment reveals it, so a
 * banner keyed only on `isSupabaseConfigured()` would report "live" while a
 * clinician reads fiction. Both cases are surfaced.
 */

/** Datasets served from mocks even when Supabase is configured, by role. */
const ALWAYS_MOCK: Record<UserRole, string[]> = {
  patient: [],
  ips: ["la lista de pacientes", "las alertas de cada paciente"],
  admin: ["las métricas del sistema", "los documentos RAG", "la lista de usuarios"],
};

export type DemoNotice =
  | { level: "all" }
  | { level: "partial"; datasets: string[] }
  | null;

export function demoNoticeFor(role: UserRole): DemoNotice {
  if (!isSupabaseConfigured()) {
    return { level: "all" };
  }
  const datasets = ALWAYS_MOCK[role];
  return datasets.length ? { level: "partial", datasets } : null;
}

const warned = new Set<string>();

/**
 * Logs once per process per source. Deliberately `warn`, not `info`: serving
 * invented clinical data is not a routine event.
 */
export function warnDemoData(source: string) {
  if (warned.has(source)) {
    return;
  }
  warned.add(source);
  console.warn(
    `[homecare] DATOS DE DEMOSTRACIÓN: ${source} proviene de lib/mock-data.ts, no de Supabase. ` +
      `No es información clínica real.`,
  );
}
