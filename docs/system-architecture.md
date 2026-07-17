# System Architecture

The project is organized around a simple pipeline:

```text
Field sensing -> Data records -> AI capabilities -> Research projects -> Conservation decisions
```

## Field Sensing Layer

Field devices may include:

- Camera traps, infrared cameras, reCamera, and XIAO ESP32S3 Sense devices.
- Acoustic recorders and low-power sound nodes.
- GPS, VHF, LoRa, BLE, or other tracking devices.
- Weather, vegetation, water, soil, and other environmental sensors.

## Data Layer

Shared metadata makes projects easier to compare and reuse. The first schemas cover:

- Observations.
- Animal individuals.
- Device metadata.
- Deployment sites.

These schemas are intentionally small and should evolve with real projects.

## AI Capability Layer

AI modules should be reusable across projects where possible:

- Computer vision for detection, classification, tracking, and individual re-identification.
- Bioacoustics for call detection, species classification, and vocalization patterns.
- Time-series analysis for movement, environment, and behavior changes.
- Edge AI for local filtering, event detection, and low-bandwidth deployments.
- LLM-assisted analytics for summarizing notes, searching records, and supporting reports.

## Research Project Layer

Each research project should define:

- Scientific question.
- Species or taxonomic group.
- Site and sensitivity level.
- Devices and data sources.
- AI tasks and evaluation plan.
- Data governance and publication rules.

