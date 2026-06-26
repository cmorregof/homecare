# Planned Data Sources

The CARMEN-Forecast research layer is designed to support future experimentation with longitudinal public clinical datasets and, later, appropriately governed HomecareCCV longitudinal data.

Planned datasets include:

- MIMIC-IV
- MIMIC-IV-ED
- HiRID
- eICU
- AmsterdamUMCdb
- Future HomecareCCV longitudinal data collected under the project's own governance

Development constraints:

- Do not commit restricted or patient-identifiable data into this repository.
- Do not assume access to protected datasets by default.
- Only commit schemas, loaders, metadata mappings, and documentation that help structure future work.
- Obtain access to protected datasets through the official credentialing and governance channels required by each source.

Synthetic data in this module exists only for software testing, interface design, and pipeline debugging. It is not evidence of clinical performance and must not be presented as validation.
