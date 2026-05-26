# Datasets

Los datasets de entrenamiento deben descargarse manualmente desde Kaggle y ubicarse en `data/mock/`.

| Dataset | Archivo esperado | Registros | Variables | Rol |
|---|---|---:|---:|---|
| Fedesoriano Stroke Prediction | `healthcare-dataset-stroke-data.csv` | 5,110 | 12 | ACV y comorbilidades |
| Sulianova Cardiovascular Disease | `cardio_train.csv` | 70,000 | 12 | Riesgo cardiovascular, PA, colesterol, glucosa |
| Fedesoriano Heart Failure Prediction | `heart.csv` | 918 | 12 | Complemento cardiovascular |

## Flujo ETL previsto

1. Cargar los tres archivos CSV.
2. Normalizar nombres de columnas.
3. Mapear variables al esquema clínico unificado.
4. Crear variables derivadas.
5. Asignar `risk_level` con reglas MEWS iniciales.
6. Separar train, validation y test.
7. Guardar `data/processed/unified_dataset.csv`.

Los archivos reales de Kaggle no se versionan por tamaño, licencia y trazabilidad.
