"""Inferencia de CARMEN-Forecast (preliminar).

Carga el TinyTemporalTransformer exportado desde la corrida canónica de
MIMIC-IV (home cadence 6h) y estima probabilidades de deterioro clínico a
6/12/24 horas sobre el historial de signos vitales del paciente.

Dominio: entrenado en UCI (MIMIC-IV); NO validado en datos domiciliarios.
El resultado es solo para el equipo clínico — nunca se muestra al paciente.

Diferencia deliberada con el entrenamiento: en inferencia el bin de 6h en
curso (que contiene el reporte recién enviado) SÍ entra en la secuencia;
en entrenamiento cada punto usaba solo bins estrictamente anteriores. En
producción no hay fuga posible y descartar el reporte actual dejaría sin
señal a los pacientes nuevos.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from config import settings

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[1]

CONCEPT_FIELDS = {
    "heart_rate": "heart_rate",
    "spo2": "oxygen_saturation",
    "sbp": "systolic_bp",
    "dbp": "diastolic_bp",
    "resp_rate": "respiratory_rate",
    "temperature": "temperature",
    "weight": "weight_kg",
}


@lru_cache
def load_forecast_artifact(model_path: str) -> dict[str, Any] | None:
    try:
        import torch
    except ImportError:
        logger.warning("torch no está instalado; CARMEN-Forecast deshabilitado")
        return None
    path = Path(model_path)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    if not path.exists():
        logger.warning("Artefacto de Forecast no encontrado en %s; deshabilitado", path)
        return None
    try:
        artifact = torch.load(path, map_location="cpu", weights_only=False)
        model = _build_model(artifact)
        artifact["_model"] = model
        return artifact
    except Exception:
        logger.exception("No se pudo cargar el artefacto de Forecast en %s", path)
        return None


def _build_model(artifact: dict[str, Any]) -> Any:
    import torch.nn as nn

    config = artifact["config"]
    n_ch = int(config["n_ch"])
    d, heads, layers = int(config["d"]), int(config["heads"]), int(config["layers"])
    max_bins = int(config["max_bins"])
    horizons = list(config["horizons"])

    class TinyTemporalTransformer(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.inp = nn.Linear(n_ch, d)
            self.demo = nn.Linear(3, d)
            self.pos = nn.Embedding(max_bins + 1, d)
            enc = nn.TransformerEncoderLayer(
                d, heads, 4 * d, dropout=0.1, batch_first=True, norm_first=True
            )
            self.enc = nn.TransformerEncoder(enc, layers)
            self.head = nn.Linear(d, len(horizons))

        def forward(self, x, demo, pad):  # type: ignore[no-untyped-def]
            import torch

            length = x.shape[1]
            tok = torch.cat([self.demo(demo).unsqueeze(1), self.inp(x)], dim=1)
            pos = self.pos(torch.arange(length + 1, device=x.device)).unsqueeze(0)
            h = self.enc(tok + pos, src_key_padding_mask=pad)
            return self.head(h[:, 0])

    model = TinyTemporalTransformer()
    model.load_state_dict(artifact["state_dict"])
    model.eval()
    return model


def forecast_deterioration(
    vital_history: list[dict[str, Any]],
    clinical_info: dict[str, Any] | None = None,
    model_path: str | None = None,
) -> dict[str, Any] | None:
    """Devuelve {"probabilities": {"6h": p, ...}, "n_reports": n, ...} o None."""
    artifact = load_forecast_artifact(model_path or settings.forecast_model_path)
    if artifact is None or not vital_history:
        return None
    try:
        return _predict(artifact, vital_history, clinical_info or {})
    except Exception:
        logger.exception("Fallo la inferencia de Forecast; se omite el pronóstico")
        return None


def _predict(
    artifact: dict[str, Any],
    vital_history: list[dict[str, Any]],
    clinical_info: dict[str, Any],
) -> dict[str, Any] | None:
    import numpy as np
    import torch

    config = artifact["config"]
    concepts = list(config["concepts"])
    val_ch = int(config["val_ch"])
    n_ch = int(config["n_ch"])
    max_bins = int(config["max_bins"])
    bin_hours = float(config.get("bin_hours", 6))
    horizons = list(config["horizons"])
    demo_norm = config["demo_norm"]
    mu = np.asarray(artifact["normalization"]["mu"], dtype=np.float32)
    sd = np.asarray(artifact["normalization"]["sd"], dtype=np.float32)

    rows = sorted(
        (r for r in vital_history if _parse_time(r.get("recorded_at")) is not None),
        key=lambda r: _parse_time(r.get("recorded_at")),
    )
    if not rows:
        return None
    t0 = _parse_time(rows[0]["recorded_at"])
    per_bin: dict[int, dict[str, list[float]]] = {}
    for row in rows:
        hours = (_parse_time(row["recorded_at"]) - t0).total_seconds() / 3600.0
        b = int(hours // bin_hours)
        for concept, field in CONCEPT_FIELDS.items():
            value = _float_or_none(row.get(field))
            if value is not None:
                per_bin.setdefault(b, {}).setdefault(concept, []).append(value)

    if not per_bin:
        return None
    last_bin = max(per_bin)
    mat = np.zeros((last_bin + 1, n_ch), dtype=np.float32)
    cidx = {c: i for i, c in enumerate(concepts)}
    for b, by_concept in per_bin.items():
        for concept, values in by_concept.items():
            j = cidx[concept] * val_ch
            mat[b, j : j + val_ch] = (
                values[-1],
                float(np.mean(values)),
                min(values),
                max(values),
                math.log1p(len(values)),
            )
            mat[b, len(concepts) * val_ch + cidx[concept]] = 1.0

    z = (mat - mu) / sd
    mask = mat[:, len(concepts) * val_ch :]
    for c in range(len(concepts)):
        z[mask[:, c] == 0.0, c * val_ch : (c + 1) * val_ch] = 0.0
    z[:, len(concepts) * val_ch :] = mask

    # bin más reciente en la posición 0, igual que en entrenamiento
    seq = z[max(0, last_bin + 1 - max_bins) : last_bin + 1][::-1].copy()

    age = _float_or_none(clinical_info.get("age")) or 65.0
    gender_f = 1.0 if str(clinical_info.get("gender") or "").lower() in {"female", "f"} else 0.0
    hours_monitored = (_parse_time(rows[-1]["recorded_at"]) - t0).total_seconds() / 3600.0
    demo = np.array(
        [
            (age - float(demo_norm["age_center"])) / float(demo_norm["age_scale"]),
            gender_f,
            hours_monitored / float(demo_norm["hours_scale"]),
        ],
        dtype=np.float32,
    )

    x = torch.from_numpy(seq).unsqueeze(0)
    demo_t = torch.from_numpy(demo).unsqueeze(0)
    pad = torch.zeros((1, len(seq) + 1), dtype=torch.bool)
    with torch.no_grad():
        probs = torch.sigmoid(artifact["_model"](x, demo_t, pad))[0].tolist()

    return {
        "probabilities": {
            horizon.replace("y_", ""): round(float(p), 4)
            for horizon, p in zip(horizons, probs)
        },
        "n_reports": len(rows),
        "hours_monitored": round(hours_monitored, 1),
        "model": "tiny_temporal_transformer (MIMIC-IV home_6h, preliminar)",
        "domain_note": "Entrenado en UCI; no validado en datos domiciliarios.",
    }


def format_forecast_note(forecast: dict[str, Any]) -> str:
    probabilities = forecast.get("probabilities", {})
    return (
        "CARMEN-Forecast (preliminar — entrenado en UCI/MIMIC-IV, no validado en domicilio): "
        f"probabilidad de deterioro clínico 6h {probabilities.get('6h', 0):.0%} · "
        f"12h {probabilities.get('12h', 0):.0%} · 24h {probabilities.get('24h', 0):.0%}. "
        f"Basado en {forecast.get('n_reports')} reportes "
        f"({forecast.get('hours_monitored')} h de monitoreo). Uso exclusivo del equipo clínico."
    )


def _parse_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
