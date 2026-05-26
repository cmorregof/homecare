"use client";

import { FormEvent, useMemo, useState } from "react";
import { Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { processVitalReport } from "@/lib/api";
import type { RiskLevel, UserRole, VitalSigns } from "@/types";

type ChatMessage = {
  id: string;
  author: "user" | "assistant";
  text: string;
};

export function ChatShell({
  role,
  patientId,
  currentRisk,
  latestVitals,
}: {
  role: UserRole;
  patientId: string;
  currentRisk?: RiskLevel;
  latestVitals?: VitalSigns;
}) {
  const intro = useMemo(
    () =>
      role === "ips"
        ? "Soy Carmen. Puedo ayudarte a revisar pacientes, alertas y signos recientes."
        : "Soy Carmen. Puedes contarme cómo te sientes o enviarme tus signos vitales.",
    [role],
  );
  const [messages, setMessages] = useState<ChatMessage[]>([{ id: "welcome", author: "assistant", text: intro }]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = text.trim();
    if (!value || sending) {
      return;
    }
    const userMessage: ChatMessage = { id: crypto.randomUUID(), author: "user", text: value };
    setMessages((current) => [...current, userMessage]);
    setText("");
    setSending(true);

    try {
      const response = looksLikeVitals(value)
        ? (await processVitalReport({ patient_id: patientId, raw_message: value })).final_response
        : buildContextualReply(value, role, currentRisk, latestVitals);
      setMessages((current) => [...current, { id: crypto.randomUUID(), author: "assistant", text: response }]);
    } catch {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          author: "assistant",
          text: "Recibí tu mensaje, pero no pude conectar con el backend. Si es urgente, usa /emergencia en Telegram o llama al 123.",
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <section className="flex min-h-[620px] flex-col rounded-md border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-4 py-3">
        <p className="font-semibold text-ink">Carmen</p>
        <p className="text-sm text-slate-600">Agente Enfermera HomecareCCV</p>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={message.author === "user" ? "flex justify-end" : "flex justify-start"}
          >
            <div
              className={
                message.author === "user"
                  ? "max-w-[82%] rounded-md bg-clinical px-4 py-3 text-sm leading-6 text-white"
                  : "max-w-[82%] rounded-md bg-slate-100 px-4 py-3 text-sm leading-6 text-slate-800"
              }
            >
              {message.text}
            </div>
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-slate-200 p-3">
        <input
          value={text}
          onChange={(event) => setText(event.target.value)}
          className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-clinical focus:ring-2 focus:ring-teal-100"
          placeholder="Escribe aquí"
        />
        <Button type="submit" disabled={sending}>
          <Send className="h-4 w-4" aria-hidden />
          Enviar
        </Button>
      </form>
    </section>
  );
}

function looksLikeVitals(value: string) {
  const text = value.toLowerCase();
  return /\d{2,3}\s*\/\s*\d{2,3}/.test(text) || ["presion", "presión", "pulso", "glucosa"].some((item) => text.includes(item));
}

function buildContextualReply(
  value: string,
  role: UserRole,
  risk?: RiskLevel,
  latestVitals?: VitalSigns,
) {
  if (role === "ips") {
    return "Para priorizar, revisa primero pacientes en crítico y alto. Si necesitas una interpretación puntual, envíame signos como presión 160/95, pulso 90, saturación 94.";
  }
  const pressure = latestVitals?.systolic_bp && latestVitals?.diastolic_bp ? `${latestVitals.systolic_bp}/${latestVitals.diastolic_bp}` : "sin medición reciente";
  if (value.toLowerCase().includes("mareo") || value.toLowerCase().includes("dolor")) {
    return `Tu último riesgo registrado es ${riskLabel(risk)} y tu presión reciente es ${pressure}. Si el síntoma es intenso, aparece debilidad, dificultad para hablar, dolor de pecho o ahogo, busca atención inmediata.`;
  }
  return `Tengo como referencia tu presión reciente ${pressure}. Para analizar mejor, envíame tus signos completos o inicia el registro por Telegram con /vitales.`;
}

function riskLabel(risk?: RiskLevel) {
  const labels: Record<RiskLevel, string> = {
    low: "bajo",
    moderate: "moderado",
    high: "alto",
    critical: "crítico",
  };
  return risk ? labels[risk] : "pendiente";
}
