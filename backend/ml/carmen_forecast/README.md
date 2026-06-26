# CARMEN-Forecast: Anticipatory Care for Cardio-Cerebrovascular Home Monitoring

CARMEN-Forecast is a short-horizon deterioration forecasting module for HomecareCCV.

## Motivation

Current monitoring systems often react when a patient is already unstable. CARMEN-Forecast studies whether deterioration can be anticipated early enough for a human clinician or care team to intervene before the situation becomes more severe.

The initial forecast horizon is `+6 hours` because HomecareCCV already collects patient vital-sign reports every 6 hours, making short-horizon forecasting operationally aligned with the existing workflow.

## Clinical Framing

The module estimates the probability that a patient will transition to a `high` or `critical` state within the next 6 hours. Its intended use is clinical prioritization support for triage, escalation, review queues, and care-team attention in resource-constrained home monitoring settings.

CARMEN-Forecast does not diagnose, prescribe, or replace clinical judgment.

## Research Question

Can recent longitudinal patient trajectories be used to forecast short-horizon cardio-cerebrovascular deterioration and generate explainable, clinically safe alerts for resource-constrained home monitoring?

## Modeling Roadmap

- Rule-based baseline using current HomecareCCV thresholds as a conservative override and comparison baseline.
- Tabular baseline with lagged temporal summaries over the recent lookback window.
- Logistic regression, random forest, LightGBM, and gradient boosting baselines.
- GRU/LSTM or TCN sequence models once longitudinal supervision workflows mature.
- Compact temporal Transformer as an intermediate deep sequence model.
- Later exploration of Temporal Fusion Transformer and PatchTST.
- Probability calibration before clinical interpretation.
- Decision-curve analysis for clinical utility assessment.
- SHAP or related attribution methods for explainability.
- External validation before any clinical interpretation claims.

## Data Strategy

The module is designed to eventually support public or officially approved longitudinal clinical sources such as:

- MIMIC-IV
- MIMIC-IV-ED
- HiRID
- eICU
- AmsterdamUMCdb
- Synthetic demo data for software testing

Important constraints:

- Do not download or commit restricted patient datasets into this repository.
- This module should contain loaders, schemas, configuration, and documentation only for protected datasets.
- Real dataset access must be obtained through the official governance and credentialing channels of each dataset.
- Synthetic data is useful for software testing and pipeline debugging only; it must not be treated as scientific evidence.

## Target Definition

```text
Input:
  Patient trajectory over previous 24-72 hours.

Prediction time:
  Current observation time t.

Horizon:
  t + 6 hours.

Output:
  Probability of deterioration or transition to high/critical risk.

Possible labels:
  ICU transfer, death, severe vital-sign instability, clinical escalation,
  or rule-defined critical event depending on dataset availability.
```

## Safety Principles

- No autonomous diagnosis.
- No autonomous prescription.
- Human-in-the-loop escalation.
- Conservative high-risk overrides for immediate threshold breaches.
- Uncertainty-aware predictions.
- Calibration before clinical interpretation.
- Audit logs for model outputs and downstream escalation.
- Privacy-preserving development practices.
- No use of restricted clinical data in external APIs.

## Minimal Viable Experiment

The first working demo in this repository should:

- Generate synthetic longitudinal patient data.
- Create sliding prediction windows.
- Train a baseline classifier.
- Evaluate AUROC, AUPRC, sensitivity, specificity, F1, confusion matrix, Brier score, and calibration.
- Generate one example CARMEN alert object.

Run locally without secrets:

```bash
PYTHONPATH=backend python -m ml.carmen_forecast.cli demo
```

## Future Integration with HomecareCCV

This research scaffold is intentionally separate from the current operational pipeline, but it is designed to connect later to:

- Telegram reports every 6 hours.
- A backend forecasting endpoint.
- A Supabase table for forecast predictions and audit trails.
- Dashboard visualization of trajectories and forecast risk.
- Alert escalation flows.
- Additional nurse-agent and doctor-agent context for human review.

## Current Scope

This directory is a research scaffold for anticipatory care, short-horizon deterioration forecasting, and future validation with public clinical datasets plus eventual HomecareCCV longitudinal data.

It is not clinically validated, not cleared for clinical deployment, and not a substitute for clinician review.
