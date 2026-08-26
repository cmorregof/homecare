# Guía de estilo de español clínico — CARMEN · v0.2 (BORRADOR, pendiente de aprobación)

**Fuente:** agregados de CARMEN-I 1.0.1 (PhysioNet, acceso bajo proyecto CENTINELA), subconjunto
cardio-cerebrovascular: 298 documentos con NER, 280 en español puro. Ningún texto del corpus
está reproducido aquí; solo términos canónicos (≥ 3 documentos), tokens y reglas.
**Polaridad:** heurística de ventana (el corpus no trae atributos de negación). Declarar así.
**Uso:** dos bloques independientes para dos agentes. La voz con la que la enfermera habla al
paciente NO se toca con esta guía: sigue siendo colombiana y coloquial.

---

## Bloque A — Comprensión (agente enfermera: extracción y estructuración)

### A1. Familias de síntomas y sus variantes canónicas
Reconocer todas como la misma familia; normalizar al término de cabecera.

| Familia | Cabecera | Variantes observadas |
|---|---|---|
| Disnea | disnea | dificultad respiratoria, ortopnea, disnea de esfuerzo, disnea de mínimos esfuerzos, disnea paroxística nocturna (DPN), sensación disneica, falta de aire, ahogo |
| Dolor torácico | dolor torácico | opresión, dolor precordial / retroesternal / centrotorácico |
| Hipertensión / hipotensión | hipertensión arterial · hipotensión | HTA, hipertenso, hipotenso, tendencia a la hipotensión, inestabilidad hemodinámica, shock. **Excluir**: hipertensión pulmonar, portal, intracraneal |
| Insuficiencia cardiaca | insuficiencia cardiaca | IC, ICC, IC descompensada, edemas, edemas en EEII/MMII, edemas periféricos, edema agudo de pulmón, ingurgitación yugular |
| Arritmia / palpitaciones | fibrilación auricular · taquicardia · palpitaciones | FA, FA paroxística, FA rápida, taquicardia sinusal, taquicárdico/-a, arritmia, lpm |
| Isquemia coronaria | cardiopatía isquémica | IAM, infarto, SCA, angina, debut |
| Ictus / focalidad | ictus | ACV, AVC, AIT, focalidad neurológica, afasia, disartria, hemiparesia, "izquierda/derecha", "territorio", "isquémico" |
| Síncope / mareo | síncope · mareo | presíncope, pérdida de conocimiento, vértigo, inestabilidad de la marcha |
| Hipoxemia | desaturación · hipoxemia | insuficiencia respiratoria (aguda / hipoxémica / grave), sat basal, SpO₂, FiO₂, taquipneico |

### A2. Negación — problema de primer orden
En el corpus, **~1 de cada 3 menciones de disnea, dolor torácico, focalidad o edemas es una negación.**
Pistas, en orden de frecuencia: `sin X` › `no X` / `no refiere X` / `no presenta X` › `niega X` › `se descarta X` / `descartado`.
Reglas:
- Una negación detectada anula el hallazgo; no se registra como síntoma presente ni como "leve".
- La fórmula "sin focalidad neurológica" es exploración normal, no hallazgo neurológico.
- "Niega" es rara en el registro peninsular y muy frecuente en el colombiano: tratarla como negación fuerte siempre.
- Ventana: la pista suele estar en los 3–5 tokens anteriores; una pista no alcanza a la siguiente coma o conjunción sin señal explícita.

### A3. Modificadores que cambian el tier
- **Esfuerzo:** "de esfuerzo" ‹ "de mínimos esfuerzos" ‹ "en reposo" ‹ "ortopnea / DPN" (gravedad creciente).
- **Curso:** "progresiva", "empeoramiento", "brusco / súbito", "desde hace N días", "de N días de evolución", "episodio", "paroxística", "debut".
- **Estado hemodinámico:** "hemodinámicamente estable" / "tendencia a la hipotensión" / "inestabilidad hemodinámica" — esta última es señal de urgencia por sí sola.
- **Contexto respiratorio vs cardiaco:** disnea + tos + fiebre + expectoración → cuadro infeccioso respiratorio; disnea + ortopnea + edemas + ingurgitación yugular → cuadro cardiaco. La enfermera no diagnostica, pero registra los acompañantes porque el motor de riesgo los usa.

### A4. Registro: aceptar ambos, hablar en uno
| Peninsular (fuente) | Colombiano (voz del sistema) |
|---|---|
| EEII | MMII / piernas |
| dislipemia | dislipidemia |
| no refiere / sin | niega / no tiene |
| lpm | lpm / por minuto |
| sat basal | saturación sin oxígeno |

### A5. Glosario de abreviaturas (inventario CARMEN-I, ≥ 3 documentos; conteos entre paréntesis)
De ~300 tokens en mayúscula, la mitad son encabezados de sección; quedan las clínicas. La enfermera
debe expandirlas al estructurar; el médico solo usa las marcadas ★ sin expandir.

**Signos y hemodinámica:** TA (16) = PA (6) tensión/presión arterial · PAS (20) / PAD (20) · FC (22) ·
FR (14) · lpm · sat basal · IY (15) ingurgitación yugular · BEG (5) buen estado general ·
NAD (6) "no … a destacar" · EF (11) exploración física.
**Cardio ★:** ECG (45) · HTA (41) · FA (31) · IC (18) / ICC (13) · IAM (11) · FEVI (24) / FE (13) ·
EAP (5) edema agudo de pulmón · RS (8) ritmo sinusal · AC (8) auscultación cardiaca ·
QT / QRS / PR / ST (intervalos ECG) · TEP (45) tromboembolismo pulmonar · TVP (15).
**Neuro ★:** ICTUS (11) · ACV (3) · NIHSS (5) · TCE (5) · HSA (3) · SNC (7).
**Respiratorio y oxígeno:** AR (10) auscultación respiratoria · MVC (8) murmullo vesicular conservado ·
VMK (34) mascarilla Venturi · VMNI (7) / VMI (7) · CPAP (6) · PEEP (4) · IOT (27) intubación ·
GSA (15) gasometría arterial · PAFI (5) · FiO₂ · SDRA (5) · EPOC (32) · SAHS (6).
**Comorbilidad:** DM (11) · ERC (10) / IRC (6) · FG (31) filtrado glomerular · HD (11) hemodiálisis ·
DLP (3) dislipemia · IMC (6) · VIH (16).
**Fármacos y vías:** AAS (21) aspirina [Colombia: ASA] · HBPM (11) · INR (13) · ATB (8) · PDN (5) /
MPDN (4) / DXM (5) corticoides · VO (5) · IV (27) / EV (6) · SC (3) · IM (8) · PRN (4).
**Anatomía:** EEII (22) [Colombia: MMII (9)] · LLSS / LLII (10 / 7) lóbulos pulmonares · ABD (19).
**Contexto asistencial:** **HDOM (31) hospitalización domiciliaria** · UCI (43) · CCEE (8) consultas
externas · planta / sala · IQ (12) intervención quirúrgica · EXITUS (5).
**Imagen y laboratorio (solo reconocer):** TC / TAC / TACAR · RM / RMN · RX · ETT (ecocardiograma) ·
PCR · LDH · GGT · DD (19) dímero D · AGA · AKIN (7) escala de daño renal.

Ambigüedades que la enfermera debe resolver por contexto: **IC** (insuficiencia cardiaca / intervalo de
confianza), **FE** (fracción de eyección / fecha), **PA** (presión arterial / pulmón-abdomen), **TA**,
**AC / AR** (auscultación cardiaca / respiratoria). **HTA, FA, FC, FR, IAM, ACV, ECG** son unívocas.

---

## Bloque B — Producción (agente médico: resumen para el clínico humano)

### B1. Estructura de nota clínica real
Secciones, en este orden, con la longitud que tienen las notas reales:
1. **Proceso actual** — 110–280 palabras (mediana 180).
2. **Antecedentes** — solo los que pesan en el tier (HTA, FA, cardiopatía isquémica, IC, ACV previo, diabetes, dislipidemia).
3. **Signos / exploración reportada** — 90–190 palabras (mediana 130). Con valores y hora de toma; declarar staleness.
4. **Impresión de riesgo y acción** — tier, motivo en una línea, override activo si lo hubo.

### B2. Negativos pertinentes, siempre explícitos
Cerrar el proceso actual con la fórmula de negativos relevantes al cuadro, p. ej. para disnea: "sin dolor torácico, sin ortopnea, sin edemas, sin fiebre". Es lo que el clínico lee primero para descartar.

### B3. Abreviaturas
Usar solo las estándar de la tabla A1 (HTA, FA, IAM, ICC, ACV, ECG, SpO₂, lpm). Cualquier otra, expandida. No inventar siglas.

### B4. Lo que el médico LLM NO escribe
Diagnóstico nominal como conclusión ("tiene un IAM"), prescripción, dosis. Escribe hallazgos, riesgo, y la recomendación de escalamiento — el diagnóstico es del clínico humano.

---

**Trazabilidad:** generada a partir de `carmen_i_recon.py` v1.2, `aggregates.json` + `style_*.csv` 26-ago-2026, verificador anti-fuga en OK. Pendiente: corrección de tokens truncados en colocaciones (script v1.3); no afecta el contenido de esta guía.
