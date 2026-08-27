# CARMEN · HomecareCCV — Estado del proyecto (27 de agosto de 2026)

Documento de contexto: qué es el sistema, qué está desplegado y verificado, con qué
números, y qué sigue. Escrito como fuente de verdad tras el ciclo intensivo del
17–27 de agosto de 2026, en vísperas del póster P100 en AIiH 2026 (Imperial College London).

---

## 1. Qué es

**CARMEN** (HomecareCCV, proyecto Minciencias 56031, Universidad Nacional de Colombia —
Manizales) es un sistema multiagente de monitoreo domiciliario y triage para pacientes
cardio-cerebrovasculares en contextos de bajos recursos (foco territorial: Atlántico,
Colombia). El paciente reporta signos vitales cada 6 horas por Telegram — sin app, con
un kit de ~COP 165.000 (~US$50) — y el sistema estratifica riesgo, pronostica deterioro,
genera reporte clínico y alerta al médico asignado. **El clínico humano siempre decide.**

- Repo: https://github.com/cmorregof/homecare
- Bot (producción): https://t.me/project918_homecare_bot
- Backend: https://carmen.up.railway.app (Railway, auto-deploy desde `main`, health `/health`)
- Dashboard: https://homecare-bice-beta.vercel.app (Vercel)
- Datos: Supabase (Postgres + Auth + pgvector + RLS)

### Filosofía de diseño (la tesis del proyecto)

> **El LLM es la boca y los oídos; el núcleo determinista es el cerebro de seguridad;
> el humano es el decisor.**

1. **Overrides duros por encima de cualquier modelo**: umbrales críticos deterministas
   (PAS ≥180/<80, FC >130/<40, SpO2 <88, glucosa >400/<50 cuando se reporta) que solo
   pueden SUBIR el tier. "No model consulted: correct by construction."
2. **Fallas ruidosas, degradación segura**: todo componente LLM/ML cae a un respaldo
   determinista auditado, con WARNING en logs. Nada falla en silencio.
3. **LLM como interfaz**: GPT-4o redacta y escucha (voz "abuelita" colombiana, extracción
   tolerante de respuestas libres), pero jamás valida rangos, cambia cifras ni decide tiers.
4. **El pronóstico requiere verificación humana**: CARMEN-Forecast va solo al médico,
   etiquetado como preliminar, nunca al paciente.

---

## 2. Arquitectura desplegada

**Flujo por reporte** (LangGraph): `validate_vitals → save_to_db → call_ml_script
(+ hard overrides) → compute_forecast → call_doctor_agent (RAG + GPT-4o) →
check_alert → send_alerts → build_response (voz LLM)`.

| Componente | Implementación | Estado |
|---|---|---|
| Intake guiado (11 campos: PA, FC, FR conteo-30s×2, SpO2, temp, peso, glucosa, dolor/mareo/disnea 0-10) | ConversationHandler + preguntas redactadas por LLM + extractor LLM de respuestas libres ("noventaysiete"→97), validadores deterministas con la última palabra | ✅ producción |
| Registro self-service | Frase natural → extrae nombre+documento → cuenta Supabase Auth + perfil → asigna médico (menos cargado, solo médicos con Telegram vinculado) → notifica al médico | ✅ producción |
| Motor de riesgo | LightGBM 4 tiers + SHAP, en-proceso, con `apply_hard_overrides` encima (ambas rutas: modelo y fallback de reglas) | ✅ producción |
| CARMEN-Forecast | TinyTemporalTransformer (d=96, 3 capas) servido en CPU; p(deterioro) a 6/12/24h sobre el historial bineado a 6h; alerta al médico si p(6h) ≥ 0.5 (`FORECAST_ALERT_THRESHOLD`) | ✅ producción |
| Agente médico | GPT-4o + RAG (pgvector; fall-through léxico local), estructura de nota clínica CARMEN-I (Bloque B), NO DIAGNOSIS / NO PRESCRIPTION en prompts y verificado por tests | ✅ producción |
| Voz de Carmen | GPT-4o reescribe borradores deterministas: abuela paisa ("¡Kiubo, mijito! 👵"), seria y protectora en crítico (guarda: si pierde urgencias/123 → plantilla dura) | ✅ producción |
| Alertas | high/critical → Telegram (paciente: humanizada; médico: clínica) + Resend email; registradas en `alerts` | ✅ verificado con teléfonos reales |
| Base RAG | 16 extractos literales (pdftotext, sin LLM) con procedencia SHA256: MINSALUD GPC HTA 2013/2017/**2025**, ACV 2015 (+NIHSS), dislipidemias 2014 (Framingham Colombia ×0.75), lineamientos ECV 2026, NEWS2 (RCP), MEWS (CC BY) | ✅ commiteado |
| Chat web del dashboard | Mismo pipeline que Telegram vía `POST /agents/chat` | ✅ |
| CI | GitHub Actions corre la suite completa en cada push/PR (torch CPU incluido) | ✅ verde |
| Tests | **85** (78 backend + 7 forecast en proceso aparte por conflicto libomp en macOS) | ✅ |

---

## 3. Resultados (los números defendibles)

### 3.1 Estratificación de riesgo — validación con outcomes reales
Nunca contra nuestra propia regla; la regla MEWS/Framingham queda como baseline auditado.

| Cohorte | n | Mejor modelo | AUROC | AUROC regla |
|---|---:|---|---:|---:|
| Stroke | 4.253 | Regresión logística | 0.77 | 0.58 |
| Cardiovascular | 68.651 | Gradient Boosting | 0.80 | 0.72 |
| Heart Failure | 918 | CatBoost | 0.91 | 0.55 |

Con guardas de fuga, calibración, curvas de decisión, subgrupos y bootstrap
(`backend/ml/models/real_outcomes/real_outcome_results.json`).

### 3.2 CARMEN-Forecast (pronóstico de deterioro)
- **Validación canónica (MIMIC-IV, 94.458 estancias UCI, 1.32M puntos, GroupKFold×5
  por sujeto): AUROC OOF 0.79 / 0.78 (6h/12h)** a cadencia domiciliaria de 6h, con las
  7 señales que el intake recoge (FC, SpO2, PAS, PAD, FR, temp, peso).
- Artefacto desplegado: fit final de la corrida canónica; AUROC validación interna
  0.796/0.785/0.768 (6/12/24h). `backend/ml/models/carmen_forecast_tfm_home6h.pt`
  (pesos + normalización + config + procedencia). Exportador:
  `mimic-iv-3.1/carmen_export_transformer.py`.
- **Umbral de alerta derivado de datos**: p(6h) ≥ 0.5 dispara en el 6.2% de los
  controles con **PPV 0.61 vs prevalencia 0.19** (sensibilidad 0.20) — 3× la señal base.
- **Chequeo cold-start externo (nuevo, 27-ago)**: el artefacto desplegado, zero-shot
  sobre **384.839 visitas de triage de MIMIC-IV-ED** (una sola toma de signos, análogo
  al primer reporte del bot): **AUROC 0.65/0.66/0.67** (6/12/24h) contra admisión/éxitus
  vs alta; mediana de p(6h) **monótona con acuity ESI** (0.111 → 0.035) y 3× entre
  EXPIRED y HOME. Script: `mimic-iv-3.1/carmen_ed_single_report_check.py`.
  Lectura: hay señal desde el primer reporte; el poder completo llega con historial.
- Etiquetado en todas partes como **preliminar: entrenado en UCI, no validado en
  domicilio**. El label es deterioro clínico compuesto — NO "ACV a 6h".

### 3.3 Diseño de lenguaje con CARMEN-I
Prompts de ambos agentes diseñados con **estadísticas agregadas** de CARMEN-I 1.0.1
(PhysioNet, acceso bajo proyecto CENTINELA): familias canónicas de síntomas, patrones de
negación (~1/3 de menciones de disnea/dolor torácico/focalidad son negaciones),
modificadores de gravedad, glosario de abreviaturas, longitudes de sección. **Ningún
texto del corpus se almacena, reproduce ni envía a servicios externos**; agregados
generados localmente con verificador anti-fuga. Guía:
`docs/guia_estilo_carmen_i_v0.1.md`. La capa coloquial colombiana (A6: "maluco",
"el corazón me brinca", "boca torcida"→ictus urgente) es diseño propio **mapeado hacia**
las familias del corpus (el corpus es clínico peninsular; no contiene slang de paciente).
Evaluación de seguridad en curso: 100 viñetas, dos fases ciegas, endpoint critical-miss.

### 3.4 Ensayo general en vivo (26-27 ago)
Circuito completo verificado con teléfonos reales (Carlos como paciente, Juan Camilo
Arias como médico): registro natural en un turno → asignación + notificación al médico →
reporte normal 🟢 → reporte crítico (FC 138, SpO2 87) → override → 🚨 + alerta al médico
con signos → **aviso de Forecast al médico (p(6h)=58%) pidiendo verificación** → reporte
clínico + nota de forecast en dashboard. Médicos del piloto: Pablo Benjumea, Juan Camilo
Arias (+ Carlos como tercero para demos).

---

## 4. La historia de ingeniería (evidencia empírica de la tesis)

El diagnóstico del 17-ago encontró el endpoint sirviendo un modelo legado sin overrides
(SpO2 84 → "low" con p=1.00) y fallas silenciosas por todas partes. En el ciclo 25-27
ago se implementó todo lo anterior y, gracias a las fallas ruidosas + ensayo general,
se cazaron **defectos latentes que llevaban meses invisibles**:

1. El agente médico GPT **nunca había funcionado** (bug `response_format json_object`
   sin la palabra "json" → 400 silencioso → siempre fallback).
2. El bot **nunca usó el modelo ML** (self-llamada HTTP a un puerto inexistente en
   Railway → siempre reglas). Fix: predicción en-proceso.
3. El **RAG siempre estuvo vacío** (tabla sin sembrar, ingesta sin caller, vacío sin
   fall-through).
4. El webhook de Telegram quedó apuntando a un dominio muerto tras un cambio de dominio.
5. `python:3.12-slim` sin `libgomp1` → lightgbm no cargaba en producción (era el 500
   histórico de `/ml/predict`).

**El punto para el paper**: en cada caso el sistema degradó de forma segura (nunca una
respuesta peligrosa) y el respaldo determinista sostuvo el servicio. "Safety by
construction + noisy failures" no es retórica: es lo que permitió encontrar y corregir
todo en 72 horas. La distinción demo/sistema es esta.

---

## 5. Limitaciones honestas (decirlas antes de que las pregunten)

1. El clasificador de tiers operativo (LightGBM) está entrenado sobre labels derivados
   de la regla clínica (probabilidades ~1.0, no calibradas). Es seguro por los overrides
   y explicable por SHAP, pero su reemplazo por modelos validados con outcomes reales es
   la ruta declarada.
2. Forecast: domain shift UCI→domicilio real; "preliminar" hasta validación prospectiva.
3. No hay entorno de staging: toda prueba dispara alertas reales; cada push a `main`
   despliega producción (mitigado por CI + "Wait for CI" disponible en Railway).
4. Registro público sin fricción = sin rate-limiting ni verificación de identidad
   (correcto para demo/piloto acompañado; no para escala).
5. La vista IPS del dashboard usa pacientes mock (la vista de paciente y el centro de
   alertas son reales).
6. Un solo proceso uvicorn; RLS de Supabase sin auditar; licencia del repo sin definir.
7. Guía AHA/ASA de prevención secundaria: la vigente es **2021** (no existe "2024
   secundaria"; la 2024 es de prevención *primaria*); texto completo con paywall — en la
   base RAG hay ficha bibliográfica, no texto.

## 6. Próximos pasos priorizados

1. **Validación prospectiva silenciosa del Forecast en el piloto de Atlántico** — cada
   reporte de 6h con su outcome genera el dataset domiciliario etiquetado que hoy no
   existe públicamente. El piloto ES el instrumento de datos.
2. Evaluación de seguridad de las 100 viñetas (el sistema ya está listo para correrla).
3. Staging (segundo bot + Supabase + entorno Railway) antes de pacientes reales.
4. Ingesta vectorial del RAG a Supabase (hoy sirve por fall-through léxico local).
5. Calibración/reemplazo del tier model; decidir presentación de probabilidades al
   paciente.
6. Rate-limiting del registro; auditoría RLS; licencia.

## 7. Ángulos de paper y venues candidatos

**Contribuciones defendibles con lo que ya hay:**
- (a) Arquitectura *safety-by-construction* para triage domiciliario con LLMs
  (overrides deterministas + LLM-como-interfaz + médico-verificador) con el estudio de
  caso empírico de fallas silenciosas (§4) — ingeniería de sistemas clínicos.
- (b) CARMEN-Forecast: pronóstico de deterioro a cadencia domiciliaria (0.78-0.79 OOF en
  94k estancias) + **chequeo cold-start en 385k visitas de ED** + umbral de alerta
  derivado de OOF con PPV/tasa de disparo — con la validación prospectiva del piloto
  como siguiente paso.
- (c) Diseño de prompts clínicos informado por corpus sin fuga (CARMEN-I agregados +
  capa coloquial colombiana) + la evaluación de 100 viñetas cuando esté.

**Venues a explorar** (orden sugerido): npj Digital Medicine, JMIR / JMIR mHealth,
CHIL (Conference on Health, Inference, and Learning), ML4H (NeurIPS workshop → PMLR),
JAMIA Open, Lancet Digital Health (ambicioso), IEEE JBHI. Para (a) como experiencia de
sistema: AMIA Annual Symposium. El feedback del póster en AIiH 2026 debería decidir
entre (a) y (b) como paper principal.

---

## 8. Referencias rápidas del repo

- Overrides: `backend/utils/risk_levels.py` (`hard_override_tier`, `apply_hard_overrides`) · tests tabla A: `backend/tests/test_hard_overrides.py`
- Forecast serving: `backend/ml/forecast.py` · umbral: `FORECAST_ALERT_THRESHOLD` (0.5)
- Voz: `backend/agents/nurse_voice.py` (STYLE_ADDENDUM = personalidad; guarda de urgencia; extractor de intake)
- Prompts: `backend/agents/prompts/{nurse,doctor}_system.txt` (CARMEN-I Bloques A/B + A6 coloquial)
- Bot: `backend/bot/handlers.py` (registro, intake LLM-driven, chat web helper)
- RAG: `backend/rag/documents/` + `SOURCES.md` (procedencia SHA256)
- Seed demo Supabase: `scripts/demo_reset_seed.sql` · diagnóstico OpenAI: `scripts/check_openai.py`
- Investigación: `mimic-iv-3.1/` (pipelines, `carmen_export_transformer.py`, `carmen_ed_single_report_check.py`) · `spanish_agent/` (CARMEN-I, agregados, guía de estilo)
