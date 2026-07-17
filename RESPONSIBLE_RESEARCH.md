# Responsible Wildlife AI Research

AI can help wildlife research, but it can also create risk when data is misused, misinterpreted, or shared without context. This repository follows a cautious approach.

## Sensitive Data

Treat the following as sensitive by default:

- Exact locations of endangered or threatened species.
- Nesting, denning, breeding, or migration sites.
- Images, audio, or metadata that can expose illegal wildlife trade targets.
- Field staff identities, private land access, and community knowledge.
- Unreleased datasets owned by research partners.

## Data Sharing Levels

| Level | Description | Example |
|---|---|---|
| Public | Safe to publish openly | Synthetic data, common species in non-sensitive sites |
| Delayed | Publish after a time window | Migration observations after the season ends |
| Generalized | Publish at coarse resolution | Region-level location instead of coordinates |
| Controlled | Access requires approval | Endangered species locations or partner-owned data |
| Restricted | Do not publish | Active nest sites, anti-poaching-sensitive data |

## Model Use

- Report uncertainty and known failure modes.
- Avoid presenting model outputs as final ecological conclusions without expert review.
- Validate models across species, regions, seasons, and device types where possible.
- Record training data provenance and annotation quality.
- Avoid deploying automated interventions without human oversight.

## Field Deployment

- Follow local laws, permits, and institutional review requirements.
- Minimize disturbance to animals and habitats.
- Consider battery, weather, maintenance, theft, and connectivity constraints.
- Plan for data loss, device failure, and safe retrieval.

