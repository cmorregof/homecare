"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatClinical } from "@/lib/utils";
import type { VitalSigns } from "@/types";

/**
 * Vitals trend. No precedent in the reference — it has no charts — so the
 * language is extended: the `.card` surface, and stroke colours read from the
 * CSS custom properties declared in globals.css. Recharts takes SVG paint
 * values rather than class names, which is why the tokens are mirrored as
 * custom properties as well as Tailwind utilities.
 *
 * The two pressure series stay inside the brand family because they are one
 * measure; pulse is a different measure and takes a neutral tone plus a dashed
 * stroke, so the three are separable without relying on hue. Red is not used:
 * in this product it means critical risk, and a pulse line is not a verdict.
 */
export type VitalThreshold = {
  value: number;
  label: string;
};

function formatHour(value?: string) {
  if (!value) {
    return "";
  }
  return formatClinical(value, { month: "short", day: "2-digit", hour: "2-digit" });
}

export function VitalsLineChart({
  data,
  thresholds,
}: {
  data: VitalSigns[];
  /**
   * Optional reference lines. Deliberately a prop and not a constant: the
   * clinical thresholds live in the backend (utils/risk_levels.py) and are not
   * exposed to the frontend today. Hardcoding them here would put a second,
   * silently diverging copy in the client. Left unwired until an endpoint
   * serves them.
   */
  thresholds?: VitalThreshold[];
}) {
  const rows = [...data].reverse().map((item) => ({
    time: formatHour(item.recorded_at),
    sistolica: item.systolic_bp,
    diastolica: item.diastolic_bp,
    pulso: item.heart_rate,
  }));

  return (
    <div className="h-80 rounded-lg border border-border bg-surface p-5 shadow-sm">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="time" tick={{ fontSize: 12, fill: "var(--muted)" }} stroke="var(--border)" />
          <YAxis tick={{ fontSize: 12, fill: "var(--muted)" }} width={36} stroke="var(--border)" />
          <Tooltip
            contentStyle={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
              boxShadow: "var(--shadow-md)",
              fontSize: 13,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 13 }} />
          {thresholds?.map((threshold) => (
            <ReferenceLine
              key={threshold.label}
              y={threshold.value}
              stroke="var(--risk-high)"
              strokeDasharray="4 4"
              label={{ value: threshold.label, fontSize: 11, fill: "var(--risk-high)", position: "insideTopRight" }}
            />
          ))}
          <Line type="monotone" dataKey="sistolica" name="Sistólica" stroke="var(--primary-dark)" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="diastolica" name="Diastólica" stroke="var(--primary)" strokeWidth={2} dot={false} />
          <Line
            type="monotone"
            dataKey="pulso"
            name="Pulso"
            stroke="var(--muted)"
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
