# Modeling Plan

The initial modeling plan is staged to preserve scientific caution and avoid disrupting the current HomecareCCV operational ML layer.

## Phase 1: Research Scaffold

- Conservative rule baseline using existing HomecareCCV thresholds
- Tabular temporal features from recent lookback windows
- Classical ML baselines such as logistic regression, random forest, gradient boosting, and LightGBM
- Basic calibration reporting
- Decision-curve analysis scaffolding

## Phase 2: Sequence Modeling

- GRU/LSTM sequence models
- Temporal convolutional networks
- Compact temporal Transformer

## Phase 3: Advanced Temporal Models

- Temporal Fusion Transformer
- PatchTST
- More formal uncertainty estimation
- Deeper explainability workflows such as SHAP for sequence models when appropriate

## Validation Priorities

- External validation on public longitudinal datasets
- Cohort-specific label definitions
- Calibration and threshold selection before interpretation
- Decision curves for clinical utility analysis
- Dataset shift analysis before any operational use

## Integration Path

Future integration points include a backend forecasting endpoint, Supabase forecast storage, dashboard visualization of trajectory plus predicted risk, and human-in-the-loop alerting that complements the existing nurse and doctor agent workflows.
