from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from config import settings
from rag.retriever import ClinicalRetriever
from utils.risk_levels import RISK_LEVELS, normalize_risk_level


PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "doctor_system.txt"


class DoctorAgent:
    def __init__(
        self,
        retriever: ClinicalRetriever | None = None,
        openai_client: AsyncOpenAI | None = None,
    ) -> None:
        self.retriever = retriever or ClinicalRetriever()
        self.openai_client = openai_client

    async def generate_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        risk_level = normalize_risk_level(payload.get("risk_level"))
        query = self._build_rag_query(payload)
        rag_sources = await self.retriever.retrieve(query, match_count=5)

        if settings.openai_api_key:
            try:
                return await self._generate_with_openai(payload, rag_sources)
            except Exception:
                return self._fallback_report(payload, rag_sources)
        return self._fallback_report(payload, rag_sources)

    async def _generate_with_openai(
        self,
        payload: dict[str, Any],
        rag_sources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        client = self.openai_client or AsyncOpenAI(api_key=settings.openai_api_key)
        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        user_payload = {
            "patient_clinical_info": payload.get("patient_clinical_info", {}),
            "vital_signs": payload.get("vital_signs", {}),
            "risk_level": normalize_risk_level(payload.get("risk_level")),
            "risk_probability": payload.get("risk_probability"),
            "shap_values": payload.get("shap_values", {}),
            "top_risk_factors": payload.get("top_risk_factors", []),
            "rag_context": rag_sources,
            "output_contract": {
                "interpretation": "texto",
                "risk_evaluation": "texto",
                "recommendations": "texto",
                "follow_up_actions": "texto",
            },
        }
        response = await client.chat.completions.create(
            model="gpt-4o",
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=False),
                },
            ],
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        return {
            "interpretation": parsed.get("interpretation", ""),
            "risk_evaluation": parsed.get("risk_evaluation", ""),
            "recommendations": parsed.get("recommendations", ""),
            "follow_up_actions": parsed.get("follow_up_actions", ""),
            "rag_sources": _public_sources(rag_sources),
            "agent_response_full": content,
        }

    def _fallback_report(
        self,
        payload: dict[str, Any],
        rag_sources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        vital_signs = payload.get("vital_signs", {})
        risk_level = normalize_risk_level(payload.get("risk_level"))
        risk = RISK_LEVELS[risk_level]
        factor_text = self._format_top_factors(payload.get("top_risk_factors", []))
        interpretation = (
            "Interpretación: los signos reportados fueron recibidos y comparados con "
            "umbrales de deterioro cardio-cerebrovascular. "
            f"Presión arterial {vital_signs.get('systolic_bp', 'sin dato')}/"
            f"{vital_signs.get('diastolic_bp', 'sin dato')} mmHg, "
            f"frecuencia cardíaca {vital_signs.get('heart_rate', 'sin dato')} lpm, "
            f"saturación {vital_signs.get('oxygen_saturation', 'sin dato')}% y "
            f"glucosa {vital_signs.get('glucose', 'sin dato')} mg/dL."
        )
        risk_evaluation = (
            f"Evaluación de riesgo: nivel {risk['label']} con probabilidad estimada "
            f"{float(payload.get('risk_probability') or 0):.0%}. {factor_text}"
        )
        recommendations = (
            "Recomendaciones: continuar el monitoreo, mantener reposo relativo mientras "
            "se confirma estabilidad, verificar que la medición se haya tomado correctamente "
            "y seguir las indicaciones del equipo tratante. No se recomienda modificar "
            "medicamentos desde este sistema."
        )
        follow_up_actions = risk["action"]
        if risk_level == "critical":
            follow_up_actions = "Dirigirse a urgencias o llamar al 123 en Colombia. El equipo tratante debe ser alertado."
        elif risk_level == "high":
            follow_up_actions = "Contactar al médico responsable y repetir medición según indicación clínica."

        full = "\n".join([interpretation, risk_evaluation, recommendations, follow_up_actions])
        return {
            "interpretation": interpretation,
            "risk_evaluation": risk_evaluation,
            "recommendations": recommendations,
            "follow_up_actions": follow_up_actions,
            "rag_sources": _public_sources(rag_sources),
            "agent_response_full": full,
        }

    def _build_rag_query(self, payload: dict[str, Any]) -> str:
        vital_signs = payload.get("vital_signs", {})
        risk_level = normalize_risk_level(payload.get("risk_level"))
        factors = payload.get("top_risk_factors", [])
        factor_names = " ".join(str(item.get("feature", "")) for item in factors if isinstance(item, dict))
        return (
            f"riesgo {risk_level} paciente cardio cerebrovascular "
            f"presion {vital_signs.get('systolic_bp')} {vital_signs.get('diastolic_bp')} "
            f"frecuencia cardiaca {vital_signs.get('heart_rate')} "
            f"saturacion {vital_signs.get('oxygen_saturation')} glucosa {vital_signs.get('glucose')} "
            f"{factor_names} MEWS Framingham ACV Colombia"
        )

    def _format_top_factors(self, factors: Any) -> str:
        if not factors:
            return "No se identificaron factores dominantes en la predicción disponible."
        names = []
        for item in factors[:3]:
            if isinstance(item, dict) and item.get("feature"):
                names.append(str(item["feature"]))
        if not names:
            return "No se identificaron factores dominantes en la predicción disponible."
        return f"Factores que más aportan al riesgo: {', '.join(names)}."


def _public_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "title": source.get("title"),
            "source": source.get("source"),
            "chunk_index": source.get("chunk_index"),
            "similarity": source.get("similarity"),
            "metadata": source.get("metadata", {}),
        }
        for source in sources
    ]
