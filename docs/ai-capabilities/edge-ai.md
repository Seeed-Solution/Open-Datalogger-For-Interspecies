# Edge AI

Edge AI runs models near the data source, which can reduce bandwidth, storage, power consumption, and manual review load.

## Useful Edge Tasks

- Empty-frame filtering.
- Motion or sound event triggering.
- Lightweight species or object detection.
- Local data summarization.
- Priority upload in low-connectivity sites.

## Constraints

- Power budget.
- Thermal conditions.
- Memory and storage.
- Model update process.
- Recovery after failure.
- Weatherproofing and physical access.

## Recommended Practice

- Keep raw data when feasible, especially during validation.
- Log model version and configuration.
- Design fallback behavior if inference fails.
- Avoid irreversible filtering until the model is trusted.

