from __future__ import annotations


class SequenceForecasterBase:
    """Shared placeholder interface for future sequence models."""

    def fit(self, sequences, targets):
        raise NotImplementedError("Sequence models are future work in this research scaffold.")

    def predict_proba(self, sequences):
        raise NotImplementedError("Sequence models are future work in this research scaffold.")


class GRULSTMForecaster(SequenceForecasterBase):
    """Placeholder for GRU/LSTM deterioration forecasting."""


class TCNForecaster(SequenceForecasterBase):
    """Placeholder for temporal convolutional network forecasting."""
