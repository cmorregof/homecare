# Flujo de los agentes IA

## Estado compartido

```python
{
    "patient_id": str,
    "raw_message": str,
    "vital_signs": dict,
    "vital_sign_id": str,
    "risk_level": str,
    "risk_probability": float,
    "shap_values": dict,
    "clinical_report": str,
    "recommendations": str,
    "alert_sent": bool,
    "final_response": str,
}
```

## Grafo del Agente Enfermera

```text
validate_vitals
  │
  ▼
save_to_db
  │
  ▼
call_ml_script
  ├──────────────► check_alert_needed ──► send_alerts
  │                                      │
  ▼                                      │
call_doctor_agent                       │
  │                                      │
  └────────────────► build_response ◄───┘
                       │
                       ▼
              respond_to_patient
```

## Contrato con el Agente Médico

Entrada:

```json
{
  "vital_signs": {},
  "risk_level": "high",
  "risk_probability": 0.78,
  "shap_values": {},
  "patient_clinical_info": {}
}
```

Salida:

```json
{
  "interpretation": "...",
  "recommendations": "...",
  "follow_up_actions": "...",
  "rag_sources": []
}
```

## Reglas de seguridad

- El Agente Enfermera no diagnostica ni prescribe.
- El Agente Médico no cambia tratamientos ni formula medicamentos.
- Todo riesgo alto o crítico genera alerta al médico responsable.
- Todo error externo debe producir una respuesta clara y empática al paciente.

## Implementación Sprint 3

- `backend/agents/nurse_agent.py`: valida signos, persiste, llama ML, consulta al médico, registra alertas y construye respuesta final.
- `backend/agents/doctor_agent.py`: recupera contexto RAG, llama OpenAI si hay API key y usa fallback clínico conservador si falla.
- `backend/agents/graph.py`: usa LangGraph cuando está instalado y un ejecutor compatible para desarrollo local sin dependencias instaladas.
- `backend/api/routes/agents.py`: expone `POST /agents/vital-report`.
