from __future__ import annotations

from ml.carmen_forecast.sequence_models import SequenceForecasterBase


class TemporalTransformerForecaster(SequenceForecasterBase):
    """Placeholder for compact temporal Transformer forecasting."""


class FutureWorkForecasters:
    """Named placeholders for later exploration once longitudinal datasets are available."""

    temporal_fusion_transformer = "TODO: evaluate Temporal Fusion Transformer when real longitudinal data is ready."
    patchtst = "TODO: evaluate PatchTST after compact transformer baselines and calibration."
