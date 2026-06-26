# Estratificación de riesgo

La estratificación combina criterios de deterioro clínico tipo MEWS, riesgo cardiovascular inspirado en Framingham adaptado al contexto colombiano y reglas de alerta inmediata para signos vitales críticos.

| Nivel | Etiqueta | MEWS | Framingham | Acción |
|---|---|---:|---:|---|
| low | 🟢 BAJO | 0-2 | < 5% | Monitoreo rutinario cada 6 horas |
| moderate | 🟡 MODERADO | 3-4 | 5-9% | Aumentar vigilancia y contactar si persiste |
| high | 🔴 ALTO | 5-6 | > 9% | Notificar al médico responsable |
| critical | 🚨 CRÍTICO | ≥ 7 | Riesgo inminente | Urgencias o línea 123 Colombia |

## Umbrales críticos inmediatos

| Variable | Crítico |
|---|---|
| Presión sistólica | > 180 mmHg o < 80 mmHg |
| Frecuencia cardíaca | > 130 lpm o < 40 lpm |
| Saturación de oxígeno | < 88% |
| Glucosa | > 400 mg/dL o < 50 mg/dL |

## Regla clínica conservada como baseline auditado

La regla MEWS/Framingham ya no se usa como target principal de entrenamiento
ML. Se conserva como score clínico interpretable para:

- orientar alertas operativas del bot;
- comparar el modelo contra un baseline clínico explícito;
- calcular curvas de decisión;
- auditar si el ML aporta discriminación/utilidad más allá de reglas simples.

El rediseño metodológico entrena modelos por cohorte contra outcomes reales:
`stroke`, `cardio` y `HeartDisease`. El score-regla se evalúa contra esos
outcomes mediante ROC-AUC, AUC-PR, Brier y beneficio neto.

```python
def assign_risk_level(row):
    score = 0
    if row["systolic_bp"] >= 180 or row["systolic_bp"] < 80:
        score += 3
    elif row["systolic_bp"] >= 160 or row["systolic_bp"] < 90:
        score += 2
    elif row["systolic_bp"] >= 140:
        score += 1

    if row["stroke_history"]:
        score += 2
    if row["heart_disease_history"]:
        score += 1
    if row["hypertension_history"]:
        score += 1
    if row["glucose"] > 300:
        score += 2
    elif row["glucose"] > 200:
        score += 1
    if row["bmi"] > 35:
        score += 1
    if row["cholesterol_level"] == 3:
        score += 1

    if score >= 7:
        return 3
    if score >= 5:
        return 2
    if score >= 3:
        return 1
    return 0
```

En `backend/ml/models/real_outcomes/real_outcome_results.json` la regla aparece
como `clinical_rule_baseline`, no como etiqueta aprendida por los modelos.
