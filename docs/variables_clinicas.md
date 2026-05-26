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

## Artefactos Sprint 2

- `data/etl/unify_datasets.py`: unifica Stroke, Cardiovascular y Heart Failure a estas 22 features.
- `backend/ml/preprocessing.py`: normaliza payloads de predicción y calcula variables derivadas.
- `backend/ml/train.py`: entrena los 10 modelos definidos y selecciona por `f1_macro`.
- `backend/ml/predict.py`: carga `best_model.pkl` una vez y responde el contrato de predicción en tiempo real.
