"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Send } from "lucide-react";

import { Alert } from "@/components/alerts/alert-row";
import { RiskPanel } from "@/components/risk/risk-badge";
import { Button } from "@/components/ui/button";
import { Field, FieldRow, TextareaField } from "@/components/ui/field";
import { Card, CardTitle } from "@/components/vitals/vital-card";
import { ApiError, processVitalReport } from "@/lib/api";
import { TELEGRAM_BOT_URL } from "@/lib/brand";
import type { RiskLevel, VitalSigns } from "@/types";

/**
 * Plausibility bounds, MIRRORED from the server's own validator
 * (backend/agents/nurse_agent.py:387-399). They exist to catch typos, not to
 * judge the reading: 35 bpm and 210 mmHg are accepted here precisely because
 * they are the values worth reporting.
 *
 * These are NOT clinical thresholds and nothing in this file decides a risk
 * tier. The tier comes from the server, which applies the model and then
 * `apply_hard_overrides` (backend/ml/predict.py:29 and :48). Keep this table
 * in step with the backend; do not tighten it locally.
 */
const BOUNDS = {
  systolic_bp: { min: 50, max: 260 },
  diastolic_bp: { min: 30, max: 160 },
  heart_rate: { min: 25, max: 220 },
  oxygen_saturation: { min: 1, max: 100 },
  respiratory_rate: { min: 6, max: 50 },
  temperature: { min: 30, max: 43 },
  weight_kg: { min: 25, max: 300 },
  glucose: { min: 20, max: 600 },
  score: { min: 0, max: 10 },
} as const;

/** The server requires these three (nurse_agent.py:378-385). */
const REQUIRED = ["systolic_bp", "diastolic_bp", "heart_rate"] as const;

type FormState = Record<string, string>;

const EMPTY: FormState = {
  systolic_bp: "",
  diastolic_bp: "",
  heart_rate: "",
  respiratory_rate: "",
  oxygen_saturation: "",
  temperature: "",
  glucose: "",
  weight_kg: "",
  pain_score: "",
  dizziness_score: "",
  dyspnea_score: "",
  notes: "",
};

type Outcome = {
  risk_level?: RiskLevel;
  risk_probability?: number;
  recommendations?: string;
  follow_up_actions?: string;
  final_response: string;
};

/** `datetime-local` wants `YYYY-MM-DDTHH:mm` in the viewer's own timezone. */
function toLocalInputValue(date: Date) {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function VitalReportForm({ patientId }: { patientId: string }) {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(EMPTY);
  const [recordedAt, setRecordedAt] = useState("");
  const [error, setError] = useState<React.ReactNode>(null);
  const [sending, setSending] = useState(false);
  const [outcome, setOutcome] = useState<Outcome | null>(null);

  // Set on the client only: rendering "now" during SSR would not match the
  // markup the browser hydrates.
  useEffect(() => {
    setRecordedAt(toLocalInputValue(new Date()));
  }, []);

  const set = (key: string, value: string) => setForm((current) => ({ ...current, [key]: value }));

  function buildVitalSigns(): VitalSigns | null {
    const numeric: Record<string, number> = {};
    for (const [key, raw] of Object.entries(form)) {
      if (key === "notes" || raw.trim() === "") {
        continue;
      }
      const value = Number(raw);
      if (Number.isNaN(value)) {
        setError(`El valor de ${LABELS[key] ?? key} no es un número.`);
        return null;
      }
      numeric[key] = value;
    }

    for (const key of REQUIRED) {
      if (numeric[key] === undefined) {
        setError(`Falta ${LABELS[key]}. Es obligatoria para generar el reporte.`);
        return null;
      }
    }

    for (const [key, value] of Object.entries(numeric)) {
      const bound = key.endsWith("_score") ? BOUNDS.score : BOUNDS[key as keyof typeof BOUNDS];
      if (bound && (value < bound.min || value > bound.max)) {
        setError(
          `${LABELS[key] ?? key}: ${value} está fuera del rango reportable (${bound.min}–${bound.max}). Revisa el dato antes de enviarlo.`,
        );
        return null;
      }
    }

    return {
      ...numeric,
      // Full instant, not a date: our recorded_at is TIMESTAMPTZ and the
      // monitoring cadence is every 6 hours (schemas.sql:101).
      recorded_at: new Date(recordedAt).toISOString(),
      ...(form.notes.trim() ? { notes: form.notes.trim() } : {}),
    };
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setOutcome(null);
    const vitalSigns = buildVitalSigns();
    if (!vitalSigns) {
      return;
    }
    setSending(true);
    try {
      const result = await processVitalReport({
        patient_id: patientId,
        raw_message: "",
        vital_signs: vitalSigns,
      });
      setOutcome(result);
      router.refresh();
    } catch (caught) {
      if (caught instanceof ApiError) {
        console.error(`[carmen] reporte no enviado (${caught.failure})`, caught.message);
      } else {
        console.error("[carmen] reporte no enviado", caught);
      }
      setError(describeFailure(caught));
    } finally {
      setSending(false);
    }
  }

  if (outcome) {
    return (
      <div className="space-y-5">
        {/* Everything shown here was decided by the server. */}
        {outcome.risk_level ? (
          <RiskPanel level={outcome.risk_level} probability={outcome.risk_probability ?? 0} />
        ) : null}
        <Card>
          <CardTitle>Respuesta de Carmen</CardTitle>
          <p className="whitespace-pre-line text-base leading-relaxed text-ink">{outcome.final_response}</p>
          {outcome.recommendations ? (
            <p className="mt-3 text-base leading-relaxed text-ink">{outcome.recommendations}</p>
          ) : null}
          {outcome.follow_up_actions ? (
            <p className="mt-3 text-base font-semibold text-muted">{outcome.follow_up_actions}</p>
          ) : null}
        </Card>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            onClick={() => {
              setOutcome(null);
              setForm(EMPTY);
              setRecordedAt(toLocalInputValue(new Date()));
            }}
          >
            Registrar otra medición
          </Button>
          <Button type="button" variant="secondary" onClick={() => router.push("/patient/history")}>
            Ver historial
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {error ? <Alert tone="error">{error}</Alert> : null}

      <Card>
        <CardTitle>Momento de la medición</CardTitle>
        <Field
          label="Fecha y hora"
          type="datetime-local"
          required
          value={recordedAt}
          onChange={(event) => setRecordedAt(event.target.value)}
          helper="Se guarda el instante completo, no solo el día."
        />
      </Card>

      <Card>
        <CardTitle>Signos vitales</CardTitle>
        <FieldRow>
          <Field
            label="Presión sistólica (mmHg)"
            type="number"
            inputMode="numeric"
            required
            min={BOUNDS.systolic_bp.min}
            max={BOUNDS.systolic_bp.max}
            value={form.systolic_bp}
            onChange={(event) => set("systolic_bp", event.target.value)}
          />
          <Field
            label="Presión diastólica (mmHg)"
            type="number"
            inputMode="numeric"
            required
            min={BOUNDS.diastolic_bp.min}
            max={BOUNDS.diastolic_bp.max}
            value={form.diastolic_bp}
            onChange={(event) => set("diastolic_bp", event.target.value)}
          />
        </FieldRow>
        <FieldRow>
          <Field
            label="Frecuencia cardíaca (lpm)"
            type="number"
            inputMode="numeric"
            required
            min={BOUNDS.heart_rate.min}
            max={BOUNDS.heart_rate.max}
            value={form.heart_rate}
            onChange={(event) => set("heart_rate", event.target.value)}
          />
          <Field
            label="Frecuencia respiratoria (rpm)"
            type="number"
            inputMode="numeric"
            min={BOUNDS.respiratory_rate.min}
            max={BOUNDS.respiratory_rate.max}
            value={form.respiratory_rate}
            onChange={(event) => set("respiratory_rate", event.target.value)}
            helper="Conteo guiado de 30 s multiplicado por 2 (Protocolo v1.0)."
          />
        </FieldRow>
        <FieldRow>
          <Field
            label="Saturación de oxígeno (%)"
            type="number"
            inputMode="numeric"
            min={BOUNDS.oxygen_saturation.min}
            max={BOUNDS.oxygen_saturation.max}
            value={form.oxygen_saturation}
            onChange={(event) => set("oxygen_saturation", event.target.value)}
          />
          <Field
            label="Temperatura (°C)"
            type="number"
            inputMode="decimal"
            step="0.1"
            min={BOUNDS.temperature.min}
            max={BOUNDS.temperature.max}
            value={form.temperature}
            onChange={(event) => set("temperature", event.target.value)}
          />
        </FieldRow>
        <FieldRow>
          <Field
            label="Glucosa (mg/dL)"
            type="number"
            inputMode="numeric"
            min={BOUNDS.glucose.min}
            max={BOUNDS.glucose.max}
            value={form.glucose}
            onChange={(event) => set("glucose", event.target.value)}
          />
          <Field
            label="Peso (kg)"
            type="number"
            inputMode="decimal"
            step="0.1"
            min={BOUNDS.weight_kg.min}
            max={BOUNDS.weight_kg.max}
            value={form.weight_kg}
            onChange={(event) => set("weight_kg", event.target.value)}
          />
        </FieldRow>
      </Card>

      <Card>
        <CardTitle>Síntomas</CardTitle>
        <p className="mb-3 text-base text-muted">De 0 (ninguno) a 10 (el peor que hayas sentido).</p>
        <FieldRow cols={3}>
          <Field
            label="Dolor"
            type="number"
            inputMode="numeric"
            min={BOUNDS.score.min}
            max={BOUNDS.score.max}
            value={form.pain_score}
            onChange={(event) => set("pain_score", event.target.value)}
          />
          <Field
            label="Mareo"
            type="number"
            inputMode="numeric"
            min={BOUNDS.score.min}
            max={BOUNDS.score.max}
            value={form.dizziness_score}
            onChange={(event) => set("dizziness_score", event.target.value)}
          />
          <Field
            label="Dificultad para respirar"
            type="number"
            inputMode="numeric"
            min={BOUNDS.score.min}
            max={BOUNDS.score.max}
            value={form.dyspnea_score}
            onChange={(event) => set("dyspnea_score", event.target.value)}
          />
        </FieldRow>
        <TextareaField
          label="Notas (opcional)"
          rows={3}
          value={form.notes}
          onChange={(event) => set("notes", event.target.value)}
          helper="Cualquier cosa que quieras que el equipo clínico sepa."
        />
      </Card>

      <Button type="submit" disabled={sending}>
        {sending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Send className="h-4 w-4" aria-hidden />}
        {sending ? "Enviando…" : "Enviar reporte"}
      </Button>
    </form>
  );
}

/**
 * Turns a failed submission into something a patient can act on.
 *
 * Every branch says the same thing first, because it is the part that matters
 * and the part the old message left out: the reading was NOT recorded. Someone
 * who took their blood pressure, saw a vague error and closed the tab would
 * otherwise believe their team had received it.
 *
 * The old message — "check your connection and try again" — blamed the reader
 * for what was in fact a misconfigured deployment, and gave no way out. Each
 * branch now offers Telegram, where CARMEN works regardless of the web app.
 *
 * The wording avoids saying the failure "was logged": it goes to the patient's
 * own browser console, which reaches nobody. Sitting beside "your reading was
 * not recorded" it also read as though the reading had been saved after all.
 */
function describeFailure(caught: unknown): React.ReactNode {
  const notSaved = <strong className="font-semibold">Tu medición no quedó registrada.</strong>;

  const viaTelegram = (
    <>
      {" "}
      Puedes reportarla por{" "}
      <a
        href={TELEGRAM_BOT_URL}
        target="_blank"
        rel="noreferrer"
        className="font-semibold underline underline-offset-2"
      >
        Telegram
      </a>{" "}
      para que tu equipo la reciba ahora.
    </>
  );

  if (caught instanceof ApiError) {
    if (caught.failure === "rejected") {
      return (
        <>
          El servidor no aceptó la medición{caught.detail ? `: ${caught.detail}` : "."} {notSaved} Revisa
          los valores y vuelve a enviarla.
        </>
      );
    }
    if (caught.failure === "server") {
      return (
        <>
          El servidor tuvo un problema al procesar la medición. {notSaved} Inténtalo de nuevo en unos
          minutos.{viaTelegram}
        </>
      );
    }
  }

  return (
    <>
      No se pudo contactar al servidor. {notSaved} Revisa tu conexión; si funciona bien, el fallo está de
      nuestro lado.{viaTelegram}
    </>
  );
}

const LABELS: Record<string, string> = {
  systolic_bp: "la presión sistólica",
  diastolic_bp: "la presión diastólica",
  heart_rate: "la frecuencia cardíaca",
  respiratory_rate: "la frecuencia respiratoria",
  oxygen_saturation: "la saturación de oxígeno",
  temperature: "la temperatura",
  glucose: "la glucosa",
  weight_kg: "el peso",
  pain_score: "el dolor",
  dizziness_score: "el mareo",
  dyspnea_score: "la dificultad para respirar",
};
