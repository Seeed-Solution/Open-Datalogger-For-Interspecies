# Data Governance

Wildlife data can create conservation value and conservation risk. This project treats governance as part of the technical design.

## Data Ownership

Every dataset should identify:

- Field data owner.
- Research institution or project.
- Collection permits or agreements.
- License or access terms.
- Publication restrictions.

## Dataset Cards

Before publishing or sharing a dataset, document:

- Species and site summary.
- Collection dates and devices.
- Annotation methods and quality checks.
- Known biases and gaps.
- Sensitive fields and masking strategy.
- Intended uses and prohibited uses.

## Location Handling

Use the least precise location that supports the research question. For sensitive species or sites, prefer:

- Region-level summaries.
- Spatial grids.
- Delayed release.
- Controlled access.
- No public release.

## Model Outputs

Model outputs should keep links to:

- Input records.
- Model version.
- Confidence score.
- Human review status.
- Known limitations.

