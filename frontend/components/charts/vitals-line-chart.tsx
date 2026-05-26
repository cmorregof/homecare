"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { VitalSigns } from "@/types";

function formatHour(value?: string) {
  if (!value) {
    return "";
  }
  return new Intl.DateTimeFormat("es-CO", { month: "short", day: "2-digit", hour: "2-digit" }).format(new Date(value));
}

export function VitalsLineChart({ data }: { data: VitalSigns[] }) {
  const rows = [...data].reverse().map((item) => ({
    time: formatHour(item.recorded_at),
    sistolica: item.systolic_bp,
    diastolica: item.diastolic_bp,
    pulso: item.heart_rate,
  }));

  return (
    <div className="h-80 rounded-md border border-slate-200 bg-white p-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="time" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} width={36} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="sistolica" name="Sistólica" stroke="#0f766e" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="diastolica" name="Diastólica" stroke="#2563eb" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="pulso" name="Pulso" stroke="#b42318" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
