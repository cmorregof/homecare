# Variables clínicas

| Variable | Descripción | Tipo | Observación |
|---|---|---|---|
| `age` | Edad del paciente | numérica | Perfil clínico |
| `gender_encoded` | Sexo codificado | categórica | 0=female, 1=male |
| `systolic_bp` | Presión arterial sistólica | numérica | mmHg |
| `diastolic_bp` | Presión arterial diastólica | numérica | mmHg |
| `heart_rate` | Frecuencia cardíaca | numérica | lpm |
| `oxygen_saturation` | Saturación de oxígeno | numérica | % |
| `glucose` | Glucosa | numérica | mg/dL |
| `bmi` | Índice de masa corporal | numérica | kg/m² |
| `cholesterol_level` | Colesterol ordinal | ordinal | 1=normal, 2=alto, 3=muy alto |
| `hypertension_history` | Antecedente de hipertensión | booleana | Historia clínica |
| `heart_disease_history` | Antecedente cardiaco | booleana | Historia clínica |
| `stroke_history` | Antecedente de ACV | booleana | Historia clínica |
| `diabetes_history` | Antecedente de diabetes | booleana | Historia clínica |
| `smoking_encoded` | Tabaquismo codificado | ordinal | 0=nunca, 1=exfumador, 2=actual |
| `alcohol_intake` | Consumo de alcohol | booleana | Historia clínica |
| `physical_activity` | Actividad física | booleana | Historia clínica |
| `pain_score` | Dolor autorreportado | ordinal | 0-10 |
| `dizziness_score` | Mareo autorreportado | ordinal | 0-10 |
| `dyspnea_score` | Disnea autorreportada | ordinal | 0-10 |
| `pulse_pressure` | Presión de pulso | derivada | sistólica - diastólica |
| `map` | Presión arterial media | derivada | diastólica + (pulso/3) |
| `bmi_category` | Categoría de IMC | derivada | 0=bajo, 1=normal, 2=sobrepeso, 3=obeso |

## Outcomes reales por cohorte

El pipeline validado no usa un `risk_level` sintético como target principal.
Cada dataset conserva su desenlace real:

| Cohorte | Outcome real | Uso correcto | Feature prohibida por leakage |
|---|---|---|---|
| Stroke | `stroke` | Target binario | `stroke_history` |
| Cardiovascular | `cardio` | Target binario | `heart_disease_history` |
| Heart Failure | `HeartDisease` | Target binario | `heart_disease_history` |

Estas columnas no se deben convertir en antecedentes clínicos dentro de la misma
cohorte. Si se incluyen como features, el modelo aprende el desenlace ya
observado y produce métricas artificialmente altas.

## Variables constantes o casi constantes

Algunas variables del esquema común son imputaciones fijas porque los datasets
públicos no contienen signos vitales longitudinales completos. El pipeline real
las audita por cohorte y las elimina si su frecuencia dominante es `>= 99,5%`.

Los detalles quedan en
`backend/ml/models/real_outcomes/real_outcome_results.json` bajo
`constant_feature_audit`.

## Artefactos Sprint 2

- `data/etl/unify_datasets.py`: unifica Stroke, Cardiovascular y Heart Failure a estas 22 features.
- `backend/ml/preprocessing.py`: normaliza payloads de predicción y calcula variables derivadas.
- `backend/ml/train.py`: conserva el pipeline legacy de riesgo sintético para compatibilidad operativa.
- `backend/ml/real_outcomes.py`: entrena y evalúa modelos por cohorte contra outcomes reales.
- `backend/ml/predict.py`: carga `best_model.pkl` una vez y responde el contrato de predicción en tiempo real.
