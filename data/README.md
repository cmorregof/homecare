# Datos para HomecareCCV

Descargar manualmente los datasets desde Kaggle y ubicarlos en `data/mock/`:

| Dataset | Archivo esperado |
|---|---|
| https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset | `healthcare-dataset-stroke-data.csv` |
| https://www.kaggle.com/datasets/sulianova/cardiovascular-disease-dataset | `cardio_train.csv` |
| https://www.kaggle.com/datasets/fedesoriano/heart-failure-prediction | `heart.csv` |

Los archivos incluidos actualmente son placeholders para conservar la estructura del repositorio. El pipeline real de unificación se implementa en el Sprint 2.

## Ejecutar ETL

```bash
PYTHONPATH=backend python data/etl/unify_datasets.py
```

Esto genera:

- `data/processed/unified_dataset.csv`
- `data/processed/train_resampled.csv`

Para una prueba técnica sin Kaggle:

```bash
PYTHONPATH=backend python data/etl/unify_datasets.py --allow-synthetic
```
