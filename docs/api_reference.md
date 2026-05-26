# API Reference

Base local: `http://localhost:8000`

## Sistema

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Health check del backend |
| GET | `/` | Metadatos básicos del servicio |
| POST | `/agents/vital-report` | Ejecuta flujo Enfermera → ML → Médico → respuesta |
| POST | `/ml/predict` | Predicción de riesgo en tiempo real |
| GET | `/models` | Resultados comparativos del entrenamiento ML |
| POST | `/webhook` | Webhook de Telegram para recibir updates del bot |
| POST | `/telegram/webhook/setup` | Configura el webhook de Telegram usando `TELEGRAM_WEBHOOK_URL` |

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
| Telegram bot | `/webhook` | Sprint 4 |

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

## ML

### POST `/ml/predict`

Request:

```json
{
  "patient_id": "uuid",
  "vital_sign_id": "uuid",
  "features": {
    "age": 72,
    "systolic_bp": 165,
    "diastolic_bp": 95,
    "heart_rate": 88,
    "oxygen_saturation": 96,
    "glucose": 130,
    "stroke_history": true,
    "hypertension_history": true
  }
}
```

Response:

```json
{
  "risk_level": "high",
  "risk_probability": 0.78,
  "probabilities": {
    "low": 0.05,
    "moderate": 0.17,
    "high": 0.78,
    "critical": 0.0
  },
  "model_used": "lightgbm",
  "shap_values": {},
  "top_risk_factors": [],
  "confidence_score": 0.61
}
```

Si `backend/ml/models/best_model.pkl` no existe, el endpoint usa reglas clínicas de seguridad como fallback y marca `model_used = clinical_rules_fallback`.

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

## Telegram

### POST `/webhook`

Recibe updates enviados por Telegram cuando el bot está configurado en modo webhook. Requiere `TELEGRAM_BOT_TOKEN`.

Request: payload nativo de Telegram.

Response:

```json
{
  "ok": true
}
```

### POST `/telegram/webhook/setup`

Configura el webhook remoto del bot usando `TELEGRAM_WEBHOOK_URL`.

Response:

```json
{
  "ok": true
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
