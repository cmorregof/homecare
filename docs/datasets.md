# Datasets

Los datasets de entrenamiento deben descargarse manualmente desde Kaggle y ubicarse en `data/mock/`.

| Dataset | Archivo esperado | Registros | Variables | Rol |
|---|---|---:|---:|---|
| Fedesoriano Stroke Prediction | `healthcare-dataset-stroke-data.csv` | 5,110 | 12 | ACV y comorbilidades |
| Sulianova Cardiovascular Disease | `cardio_train.csv` | 70,000 | 12 | Riesgo cardiovascular, PA, colesterol, glucosa |
| Fedesoriano Heart Failure Prediction | `heart.csv` | 918 | 12 | Complemento cardiovascular |

## Flujo ETL validado

1. Cargar los tres archivos CSV.
2. Normalizar nombres de columnas.
3. Mantener cada dataset como cohorte independiente.
4. Crear variables derivadas.
5. Usar el desenlace real como target: `stroke`, `cardio` o `HeartDisease`.
6. Eliminar la feature derivada del mismo desenlace para evitar leakage.
7. Auditar columnas constantes/casi constantes por cohorte.
8. Separar train, validation y test estratificados.
9. Evaluar ML contra el score-regla MEWS/Framingham como baseline.
10. Guardar `data/processed/real_outcomes/*.csv` y artefactos en `backend/ml/models/real_outcomes/`.

El flujo antiguo `unified_dataset.csv` + `risk_level` sintético queda disponible
solo como compatibilidad operativa/legacy para la estratificación de cuatro
niveles del bot.

Los archivos reales de Kaggle no se versionan por tamaño, licencia y trazabilidad.

## Comandos

Con datasets reales:

```bash
PYTHONPATH=backend python -m ml.real_outcomes --bootstrap-iterations 200
```

Smoke-test local sin Kaggle:

```bash
PYTHONPATH=backend python data/etl/unify_datasets.py --allow-synthetic
```
