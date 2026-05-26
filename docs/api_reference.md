# API Reference

Base local: `http://localhost:8000`

## Sistema

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Health check del backend |
| GET | `/` | Metadatos básicos del servicio |
| POST | `/agents/vital-report` | Ejecuta flujo Enfermera → ML → Médico → respuesta |

## Endpoints planeados

| Módulo | Ruta base | Estado |
|---|---|---|
| Pacientes | `/patients` | Sprint 5 |
| Signos vitales | `/vitals` | Sprint 3-4 |
| Predicciones | `/predictions` | Sprint 2 |
| Alertas | `/alerts` | Sprint 4 |
| Reportes | `/reports` | Sprint 3 |
| Usuarios | `/users` | Sprint 5 |
| Modelos ML | `/models` | Sprint 2 y 5 |
| ML predict | `/ml/predict` | Sprint 2 |

## Agentes

### POST `/agents/vital-report`

Ejecuta el flujo completo de Sprint 3. Si `/ml/predict` aún no está disponible, el Agente Enfermera usa reglas clínicas de fallback.

Request:

```json
{
  "patient_id": "uuid",
  "raw_message": "Presión 165/95, pulso 88, saturación 96, glucosa 130",
  "source": "telegram"
}
```

Response:

```json
{
  "patient_id": "uuid",
  "vital_sign_id": "uuid",
  "prediction_id": "uuid",
  "risk_level": "high",
  "risk_probability": 0.82,
  "recommendations": "...",
  "follow_up_actions": "...",
  "alert_sent": true,
  "final_response": "...",
  "rag_sources": []
}
```

## Health check

Respuesta esperada:

```json
{
  "status": "ok",
  "service": "homecare-ccv-backend",
  "environment": "development"
}
```
