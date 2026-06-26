# Clinical Problem

Home monitoring can reduce friction for patients with chronic cardio-cerebrovascular risk, but it also creates a surveillance gap between reports and clinician review. Patients may look stable at one report and evolve toward hypoxemia, hypertensive instability, worsening symptoms, or poor adherence before the next human touchpoint.

Anticipatory care asks a different question from conventional risk stratification. Instead of estimating only the patient's current state, it studies whether the recent longitudinal trajectory contains signals that a patient may deteriorate in the near future.

In HomecareCCV, the `+6 hour` horizon is operationally meaningful because the platform already collects patient vital signs every 6 hours through Telegram. A forecast aligned to that interval could support queue prioritization, earlier clinical review, and more efficient use of limited care-team capacity.

The target clinical domain is cardio-cerebrovascular deterioration in the home setting. Examples include worsening oxygen saturation, severe blood pressure excursions, progressive dyspnea, symptom escalation, or clinical patterns that justify human follow-up.

Human escalation matters because a forecasting system should not diagnose, prescribe, or replace clinicians. The intended role is to support review, prioritization, escalation, and clinician attention under uncertainty.
