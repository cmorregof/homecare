# Modelo ML con outcomes reales por cohorte

Este documento reemplaza el reporte anterior basado en `risk_level` sintético.
La corrida previa alcanzaba métricas cercanas a 0.99 porque el target era una
regla determinista derivada de los mismos predictores. Esa evaluación no medía
predicción clínica real; medía la capacidad del modelo de reaprender la regla.

El diseño corregido conserva la regla MEWS/Framingham como **baseline clínico
auditado**, pero el ML se entrena y evalúa contra desenlaces reales de cada
dataset:

| Cohorte | Dataset | Outcome real | Registros tras auditoría | Prevalencia |
| --- | --- | --- | ---: | ---: |
| `stroke` | Fedesoriano Stroke Prediction | `stroke` | 4.253 | 5,8% |
| `cvd` | Sulianova Cardiovascular Disease | `cardio` | 68.651 | 49,5% |
| `heart_failure` | Fedesoriano Heart Failure | `HeartDisease` | 918 | 55,3% |

## Corrección de fuga de información

Los desenlaces reales ya no se convierten en features. En cada cohorte se aplica
un guardarraíl explícito:

| Cohorte | Outcome | Feature derivada removida | Estado |
| --- | --- | --- | --- |
| `stroke` | `stroke` | `stroke_history` | Sin leakage |
| `cvd` | `cardio` | `heart_disease_history` | Sin leakage |
| `heart_failure` | `HeartDisease` | `heart_disease_history` | Sin leakage |

Además se eliminan columnas constantes o casi constantes por cohorte
(`threshold=0.995`) porque varios signos vitales son imputaciones fijas en las
fuentes públicas:

| Cohorte | Features removidas por constancia |
| --- | --- |
| `stroke` | `heart_rate`, `oxygen_saturation`, `cholesterol_level`, `diabetes_history`, `alcohol_intake`, `physical_activity`, `pain_score`, `dizziness_score`, `dyspnea_score` |
| `cvd` | `heart_rate`, `oxygen_saturation`, `stroke_history`, `pain_score`, `dizziness_score`, `dyspnea_score` |
| `heart_failure` | `oxygen_saturation`, `stroke_history`, `smoking_encoded`, `alcohol_intake`, `dizziness_score`, `dyspnea_score`, `bmi_category` |

## Suite de evaluación

Para cada cohorte/modelo se reporta:

- ROC-AUC y AUC-PR.
- Brier score, pendiente e intercepto de calibración.
- Calibración Platt/isotónica seleccionada si mejora Brier en validación.
- Curva de decisión con beneficio neto vs. tratar todos, tratar nadie y score-regla.
- Comparación explícita ML vs. score-regla MEWS/Framingham.
- Subgrupos por sexo y franjas de edad.
- SHAP/top factores para el caso de mayor probabilidad en test.
- Intervalos de confianza bootstrap en test.
- Validación cruzada estratificada y test held-out.

## Resultado principal por cohorte

| Cohorte | Mejor modelo | ROC-AUC test | AUC-PR test | Brier test | ROC regla | AUC-PR regla | Brier regla | Delta beneficio neto medio vs regla |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `stroke` | logistic_regression | 0,771 | 0,138 | 0,059 | 0,576 | 0,085 | 0,056 | +0,0007 |
| `cvd` | gradient_boosting | 0,801 | 0,775 | 0,181 | 0,720 | 0,685 | 0,203 | +0,0251 |
| `heart_failure` | catboost | 0,907 | 0,909 | 0,123 | 0,546 | 0,616 | 0,244 | +0,1013 |

## Comparativo completo por modelo

### Stroke

| Modelo | ROC-AUC validación | ROC-AUC test | AUC-PR test | Brier test | Calibración |
| --- | ---: | ---: | ---: | ---: | --- |
| logistic_regression | 0,849 | 0,771 | 0,138 | 0,059 | isotonic |
| decision_tree | 0,511 | 0,568 | 0,081 | 0,054 | sigmoid |
| random_forest | 0,727 | 0,738 | 0,122 | 0,052 | isotonic |
| gradient_boosting | 0,800 | 0,755 | 0,122 | 0,053 | isotonic |
| xgboost | 0,753 | 0,714 | 0,115 | 0,054 | isotonic |
| lightgbm | 0,775 | 0,762 | 0,138 | 0,052 | isotonic |
| catboost | 0,771 | 0,744 | 0,122 | 0,053 | isotonic |
| svm | 0,849 | 0,779 | 0,143 | 0,058 | isotonic |
| knn | 0,744 | 0,681 | 0,114 | 0,053 | isotonic |
| mlp | 0,713 | 0,723 | 0,117 | 0,055 | isotonic |

La selección se hace por ROC-AUC de validación. Por eso `logistic_regression`
queda como modelo seleccionado aunque `svm` tenga ROC-AUC de test ligeramente
mayor; el test se conserva como evaluación final, no como criterio de selección.

### Cardiovascular Disease

| Modelo | ROC-AUC validación | ROC-AUC test | AUC-PR test | Brier test | Calibración |
| --- | ---: | ---: | ---: | ---: | --- |
| logistic_regression | 0,793 | 0,796 | 0,768 | 0,183 | isotonic |
| decision_tree | 0,631 | 0,643 | 0,587 | 0,230 | sigmoid |
| random_forest | 0,759 | 0,763 | 0,734 | 0,198 | isotonic |
| gradient_boosting | 0,802 | 0,801 | 0,775 | 0,181 | isotonic |
| xgboost | 0,789 | 0,793 | 0,766 | 0,184 | isotonic |
| lightgbm | 0,801 | 0,800 | 0,773 | 0,181 | isotonic |
| catboost | 0,800 | 0,801 | 0,775 | 0,181 | isotonic |
| svm | 0,793 | 0,796 | 0,766 | 0,183 | isotonic |
| knn | 0,780 | 0,780 | 0,752 | 0,189 | isotonic |
| mlp | 0,766 | 0,759 | 0,725 | 0,199 | isotonic |

### Heart Failure

| Modelo | ROC-AUC validación | ROC-AUC test | AUC-PR test | Brier test | Calibración |
| --- | ---: | ---: | ---: | ---: | --- |
| logistic_regression | 0,869 | 0,856 | 0,871 | 0,149 | isotonic |
| decision_tree | 0,762 | 0,759 | 0,734 | 0,181 | isotonic |
| random_forest | 0,894 | 0,901 | 0,902 | 0,138 | isotonic |
| gradient_boosting | 0,861 | 0,892 | 0,882 | 0,135 | isotonic |
| xgboost | 0,850 | 0,893 | 0,890 | 0,141 | isotonic |
| lightgbm | 0,862 | 0,887 | 0,894 | 0,138 | isotonic |
| catboost | 0,895 | 0,907 | 0,909 | 0,123 | isotonic |
| svm | 0,869 | 0,854 | 0,870 | 0,144 | isotonic |
| knn | 0,871 | 0,895 | 0,895 | 0,134 | isotonic |
| mlp | 0,863 | 0,861 | 0,855 | 0,155 | isotonic |

## Artefactos versionados

```text
backend/ml/models/real_outcomes/real_outcome_results.json
backend/ml/models/real_outcomes/stroke/best_model.pkl
backend/ml/models/real_outcomes/cvd/best_model.pkl
backend/ml/models/real_outcomes/heart_failure/best_model.pkl
backend/ml/models/real_outcomes/figures/*.png
data/processed/real_outcomes/stroke.csv
data/processed/real_outcomes/cvd.csv
data/processed/real_outcomes/heart_failure.csv
docs/notebooks/homecare_ml_real_outcomes.ipynb
```

## Alineación TRIPOD+AI

El reporte se alinea con TRIPOD+AI en los puntos relevantes para esta etapa:

- Fuente de datos, cohortes y outcomes especificados.
- Separación de entrenamiento, validación y test held-out.
- Auditoría de leakage y predictores constantes.
- Reporte de discriminación, calibración y utilidad clínica.
- Comparación contra baseline clínico interpretable.
- Evaluación por subgrupos.
- Incertidumbre mediante bootstrap.
- Explicabilidad con SHAP/top factores.

## Reproducir

```bash
cd /Users/cmorregof/Personal/Contratista\ UNAL/Homecare/homecare-ccv
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
PYTHONPATH=backend .venv/bin/python -m ml.real_outcomes --bootstrap-iterations 200
```

El notebook de Colab reproduce el mismo flujo desde descarga de Kaggle hasta
figuras y JSON final.
