# Arquitectura de HomecareCCV

HomecareCCV se organiza como una arquitectura modular con un backend FastAPI, un bot de Telegram, dos agentes LangGraph, un servicio de ML en tiempo real, Supabase como capa de datos y una web app Next.js.

```text
Paciente
  │
  ▼
Telegram Bot
  │
  ▼
Agente Enfermera
  ├─ valida signos vitales
  ├─ guarda en Supabase
  ├─ llama /ml/predict
  ├─ llama Agente Médico
  ├─ dispara alertas si riesgo alto o crítico
  └─ responde al paciente

ML API
  ├─ carga best_model.pkl al iniciar
  ├─ calcula riesgo
  ├─ calcula SHAP
  └─ persiste predicción

Agente Médico
  ├─ recibe signos + riesgo + contexto clínico
  ├─ consulta RAG en pgvector
  └─ genera reporte estructurado

Supabase
  ├─ Auth
  ├─ PostgreSQL
  ├─ pgvector
  └─ Realtime

Next.js Web App
  ├─ paciente
  ├─ IPS
  └─ admin
```

## Principios de diseño

- Persistencia primero: cada reporte de signos vitales se guarda antes de ejecutar ML o LLM.
- Fallback clínico: si ML u OpenAI fallan, el sistema usa reglas clínicas básicas y responde al paciente.
- Trazabilidad: predicciones, SHAP, reportes RAG y alertas quedan auditables.
- Separación por rol: paciente, IPS y admin tienen superficies web independientes.
- No prescripción: los agentes recomiendan seguimiento y alerta, pero no cambian tratamientos.

## Fronteras de responsabilidad

| Módulo | Responsabilidad |
|---|---|
| `backend/bot` | Conversación Telegram, comandos y recordatorios |
| `backend/agents` | Orquestación clínica conversacional |
| `backend/ml` | Entrenamiento, selección, predicción y explicabilidad |
| `backend/rag` | Indexación y recuperación de guías clínicas |
| `backend/db` | Supabase, schema SQL y semillas |
| `backend/notifications` | Email y Telegram para alertas |
| `frontend` | Dashboards, autenticación y chat web |
