# 🏥 HomecareCCV

> Sistema de monitoreo domiciliario con agentes IA para pacientes
> cardio-cerebrovasculares — Universidad Nacional de Colombia

## Tabla de contenidos

1. [¿Qué es HomecareCCV?](#qué-es-homecareccv)
2. [Arquitectura del sistema](#arquitectura-del-sistema)
3. [Flujo de los agentes IA](#flujo-de-los-agentes-ia)
4. [Stack tecnológico](#stack-tecnológico)
5. [Estructura del repositorio](#estructura-del-repositorio)
6. [Datasets utilizados](#datasets-utilizados)
7. [Estratificación de riesgo](#estratificación-de-riesgo)
8. [Variables clínicas](#variables-clínicas)
9. [Modelos de ML](#modelos-de-ml)
10. [Instalación y desarrollo local](#instalación-y-desarrollo-local)
11. [Variables de entorno](#variables-de-entorno)
12. [Despliegue](#despliegue)
13. [Bibliografía](#bibliografía)
14. [Equipo de investigación](#equipo-de-investigación)
15. [Licencia](#licencia)

## ¿Qué es HomecareCCV?

HomecareCCV es una plataforma end-to-end de monitoreo en casa para pacientes con enfermedades cardio-cerebrovasculares. Combina un bot conversacional de Telegram, agentes clínicos basados en LLM, modelos de machine learning en tiempo real, RAG sobre guías clínicas y una aplicación web con dashboards por rol.

El sistema está fundamentado en el proyecto de investigación 56031 de la Universidad Nacional de Colombia sede Manizales, dirigido por la doctora Elisabeth Restrepo Parra, con financiación de Minciencias y foco territorial en el departamento del Atlántico, Colombia.

## Arquitectura del sistema

```text
PACIENTE
│
│ reporta signos vitales cada 6 horas
▼
┌─────────────────────────────────────────────────┐
│ TELEGRAM BOT                                    │
│ python-telegram-bot v20+                        │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│ AGENTE 1 - ENFERMERA                            │
│ LangGraph + OpenAI                              │
│                                                 │
│ 1. Valida y estructura signos vitales           │
│ 2. Persiste en Supabase                         │
│ 3. Llama al script ML                           │
│ 4. Llama al Agente Médico                       │
│ 5. Consolida respuesta al paciente              │
│ 6. Dispara alertas si aplica                    │
└────────────┬──────────────────┬─────────────────┘
             │                  │
             ▼                  ▼
┌────────────────────┐  ┌──────────────────────────┐
│ SCRIPT ML          │  │ AGENTE 2 - MÉDICO         │
│ FastAPI + sklearn  │  │ LangGraph + RAG           │
│ XGBoost/LightGBM   │  │ pgvector + guías clínicas │
│ CatBoost + SHAP    │  │                          │
│                    │  │ Interpreta signos, riesgo │
│ riesgo + factores  │  │ y genera reporte clínico  │
└────────────────────┘  └──────────────────────────┘
             │                  │
             └────────┬─────────┘
                      ▼
┌─────────────────────────────────────────────────┐
│ SUPABASE                                        │
│ PostgreSQL + pgvector + Auth + Realtime         │
│                                                 │
│ profiles, ips, patient_clinical_info            │
│ vital_signs, risk_predictions                   │
│ clinical_reports, alerts, rag_documents         │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│ WEB APP - Next.js 14                            │
│                                                 │
│ Paciente: historial, riesgo, recomendaciones    │
│ IPS: pacientes, alertas, reportes clínicos      │
│ Admin: usuarios, métricas, modelos, RAG         │
└─────────────────────────────────────────────────┘

ALERTAS:
  riesgo alto o crítico
  → Telegram a paciente y médico responsable
  → Email al médico responsable
```

## Flujo de los agentes IA

```text
Mensaje del paciente
        │
        ▼
validate_vitals
        │
        ▼
save_to_db
        │
        ▼
call_ml_script
        │
        ├───────────────► check_alert_needed ──► send_alerts
        │                                      │
        ▼                                      │
call_doctor_agent                              │
        │                                      │
        └──────────────────┬───────────────────┘
                           ▼
                    build_response
                           │
                           ▼
                  respond_to_patient
```

## Stack tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| Bot conversacional | python-telegram-bot v20+ | API estable y adecuada para MVP |
| Orquestación agentes | LangGraph | Estado compartido y grafo dirigido |
| LLM | OpenAI GPT-4o | Calidad clínica conversacional y tool calling |
| Embeddings RAG | text-embedding-3-small | Costo-eficiente y compatible con pgvector |
| Vector DB | Supabase pgvector | Evita un servicio vectorial adicional |
| Base de datos | Supabase PostgreSQL | Auth, Realtime y SQL administrado |
| Backend API | FastAPI | Async, tipado y OpenAPI automático |
| ML | scikit-learn, XGBoost, LightGBM, CatBoost | Comparación de 10 modelos clásicos |
| Explicabilidad | SHAP | Factores de riesgo interpretables |
| Frontend | Next.js 14, TypeScript, Tailwind CSS | App Router, SSR y UI tipada |
| Gráficos | Recharts | Visualizaciones declarativas en React |
| Email | Resend | Envío simple por API REST |
| Backend deploy | Railway | Docker y variables de entorno |
| Frontend deploy | Vercel | CI/CD para Next.js |

## Estructura del repositorio

```text
homecare-ccv/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docs/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── agents/
│   ├── ml/
│   ├── rag/
│   ├── bot/
│   ├── api/
│   ├── db/
│   ├── notifications/
│   └── utils/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── types/
├── data/
│   ├── mock/
│   ├── processed/
│   └── etl/
└── .github/
    └── workflows/
```

## Datasets utilizados

| Dataset | Fuente | Registros | Uso en el sistema |
|---|---:|---:|---|
| Stroke Prediction Dataset | Kaggle, Fedesoriano | 5,110 | Factores de ACV y comorbilidad |
| Cardiovascular Disease Dataset | Kaggle, Sulianova | 70,000 | Presión arterial, colesterol, glucosa y hábitos |
| Heart Failure Prediction | Kaggle, Fedesoriano | 918 | Complemento para riesgo cardiovascular |

## Estratificación de riesgo

| Nivel | Etiqueta | Criterios orientadores | Acción |
|---|---|---|---|
| low | 🟢 BAJO | MEWS 0-2, Framingham < 5% | Monitoreo rutinario cada 6 horas |
| moderate | 🟡 MODERADO | MEWS 3-4, Framingham 5-9% | Aumentar vigilancia y contactar si persiste |
| high | 🔴 ALTO | MEWS 5-6, Framingham > 9% | Notificar al médico responsable |
| critical | 🚨 CRÍTICO | MEWS ≥ 7 o umbral crítico inmediato | Urgencias o línea 123 Colombia |

## Variables clínicas

| Variable | Tipo | Fuente esperada |
|---|---|---|
| age | numérica | Perfil clínico |
| gender_encoded | categórica codificada | Perfil clínico |
| systolic_bp | numérica | Telegram/web/manual |
| diastolic_bp | numérica | Telegram/web/manual |
| heart_rate | numérica | Telegram/web/manual |
| oxygen_saturation | numérica | Telegram/web/manual |
| glucose | numérica | Telegram/web/manual/dataset |
| bmi | numérica | Perfil clínico/dataset |
| cholesterol_level | categórica ordinal | Perfil clínico/dataset |
| hypertension_history | booleana | Historia clínica |
| heart_disease_history | booleana | Historia clínica |
| stroke_history | booleana | Historia clínica |
| diabetes_history | booleana | Historia clínica |
| smoking_encoded | categórica codificada | Historia clínica/dataset |
| alcohol_intake | booleana | Historia clínica |
| physical_activity | booleana | Historia clínica |
| pain_score | ordinal 0-10 | Autorreporte |
| dizziness_score | ordinal 0-10 | Autorreporte |
| dyspnea_score | ordinal 0-10 | Autorreporte |
| pulse_pressure | derivada | sistólica - diastólica |
| map | derivada | presión arterial media |
| bmi_category | derivada | bajo, normal, sobrepeso, obeso |

## Modelos de ML

La métrica principal de selección es `f1_macro`, con validación cruzada de 5 folds y balanceo por SMOTE.

1. Logistic Regression
2. Decision Tree
3. Random Forest
4. Gradient Boosting
5. XGBoost
6. LightGBM
7. CatBoost
8. SVM RBF
9. KNN
10. MLP

## Instalación y desarrollo local

```bash
git clone <repo-url> homecare-ccv
cd homecare-ccv
cp .env.example backend/.env
cp .env.example frontend/.env.local
docker compose up --build
```

Para ejecutar solo el backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Variables de entorno

Las variables están documentadas en `.env.example`. Nunca se deben versionar archivos `.env`, `.env.local` ni llaves privadas.

## Despliegue

Backend en Railway:

1. Conectar el repositorio.
2. Usar `backend/Dockerfile`.
3. Configurar variables de entorno.
4. Exponer `PORT=8000` y configurar el webhook de Telegram.

Frontend en Vercel:

1. Conectar el repositorio.
2. Seleccionar `frontend/` como root directory.
3. Configurar `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` y `NEXT_PUBLIC_API_URL`.

## Bibliografía

La bibliografía completa está en `docs/bibliografia.md` e incluye Tumaini et al. (2025), Zain et al. (2024), Lv et al. (2023), Ko et al. (2025), MedAgents, ClinicalAgents, guías MINSALUD y los datasets de Kaggle.

## Equipo de investigación

Directora: Elisabeth Restrepo Parra - erestrepopa@unal.edu.co  
Universidad Nacional de Colombia, sede Manizales  
Facultad de Ciencias Exactas y Naturales  
Departamento de Física y Química  
Financiación: Minciencias Colombia  
Código proyecto: 56031

## Licencia

Pendiente de definición por el equipo de investigación y la Universidad Nacional de Colombia.
