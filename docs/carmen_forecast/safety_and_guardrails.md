# Safety And Guardrails

CARMEN-Forecast is a research scaffold for anticipatory care, not a clinically validated device or autonomous care system.

Core guardrails:

- No diagnosis generation
- No autonomous prescription or treatment changes
- Human-in-the-loop review before action
- Conservative escalation when immediate high-risk thresholds are breached
- Uncertainty awareness and calibration before interpretation
- Auditability of predictions, thresholds, and downstream alerts
- Privacy-preserving development practices
- Clinical review before any patient-facing action

Additional implementation constraints:

- Do not send restricted clinical data to external APIs as part of model development.
- Keep synthetic demo outputs clearly labeled as synthetic.
- Treat public-dataset validation and real HomecareCCV validation as separate future workstreams.
- Avoid language that implies mortality prevention, clinical readiness, or validated deployment.
