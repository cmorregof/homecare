# Entrenamiento real del modelo ML

Este documento registra el entrenamiento real de Sprint 2 usando los tres datasets descargados desde Kaggle en `data/mock/`.

## Datos usados

| Dataset | Archivo local | Registros |
| --- | --- | ---: |
| Fedesoriano Stroke Prediction | `healthcare-dataset-stroke-data.csv` | 5.110 |
| Sulianova Cardiovascular Disease | `cardio_train.csv` | 70.000 |
| Fedesoriano Heart Failure Prediction | `heart.csv` | 918 |

El ETL genero `data/processed/unified_dataset.csv` con 76.028 filas y 21 features clinicas. Durante entrenamiento, el split de entrenamiento se balanceo con SMOTE hasta 155.912 filas.

## Entorno

- Python 3.12 en `.venv`
- `numpy==1.26.4` por compatibilidad con CatBoost 1.2.7
- `scikit-learn==1.5.2` por compatibilidad con XGBoost 2.1.3
- `httpx==0.27.2` por compatibilidad con Supabase 2.10.0
- En macOS se requiere `libomp` para XGBoost y LightGBM

## Resultado comparativo

| Modelo | Estado | F1 macro validacion | F1 macro test | Filas entrenamiento |
| --- | --- | ---: | ---: | ---: |
| logistic_regression | trained | 0.7051 | 0.6860 | 155.912 |
| decision_tree | trained | 0.9724 | 0.9777 | 155.912 |
| random_forest | trained | 0.9837 | 0.9614 | 155.912 |
| gradient_boosting | trained | 0.9721 | 0.9674 | 155.912 |
| xgboost | trained | 0.9810 | 0.9785 | 155.912 |
| lightgbm | trained | 0.9870 | 0.9733 | 155.912 |
| catboost | trained | 0.9724 | 0.9772 | 155.912 |
| svm | trained | 0.6821 | 0.6502 | 12.000 |
| knn | trained | 0.6280 | 0.6220 | 12.000 |
| mlp | trained | 0.9092 | 0.8961 | 12.000 |

## Modelo seleccionado

El modelo seleccionado por `f1_macro` de validacion fue `lightgbm`, serializado en:

- `backend/ml/models/best_model.pkl`
- `backend/ml/models/comparison_results.json`

Los modelos SVM, KNN y MLP usan una muestra estratificada de 12.000 filas para mantener el entrenamiento local reproducible. La validacion y el test se calculan contra los splits completos.

## Reproducir

```bash
cd /Users/cmorregof/Personal/Contratista\ UNAL/Homecare/homecare-ccv
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
PYTHONPATH=backend .venv/bin/python data/etl/unify_datasets.py
cd backend
PYTHONPATH=. ../.venv/bin/python -m ml.train
```
