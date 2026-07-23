# Open Datalogger For Interspecies

An open-source initiative applying AI, sensing, and edge computing to wildlife research and conservation.

[中文介绍](README.zh-CN.md)

## Why This Project

Wildlife researchers collect images, video, audio, tracking signals, and environmental measurements in difficult field conditions. Much of this work still depends on manual observation, fragmented tools, and project-specific data formats.

Open Datalogger For Interspecies aims to connect real field research questions with reusable open-source AI, sensing, and edge computing patterns. The first stage of this repository is intentionally documentation-driven: define the research themes, contribution model, data schemas, and project templates before adding heavier software modules.

## Research Themes

| Theme | Core Question | AI Capabilities |
|---|---|---|
| [Individual Identification & Lifetime Tracking](docs/research-themes/01-individual-identification/README.md) | Which individual is this, and what happens across its life? | Re-ID, embeddings, tracking, life-history records |
| [Acoustic Monitoring & Stress Signals](docs/research-themes/02-acoustic-monitoring/README.md) | What sounds are animals producing, and do they indicate stress or abnormal behavior? | Bioacoustics, event detection, classification |
| [Population Monitoring](docs/research-themes/03-population-monitoring/README.md) | How many animals are present, and how is the population changing? | Detection, counting, occupancy modeling |
| [Social Behavior Networks](docs/research-themes/04-social-networks/README.md) | Who interacts with whom, and how is the group organized? | Multi-object tracking, association analysis, graph analytics |
| [Habitat Health & Carrying Capacity](docs/research-themes/05-habitat-capacity/README.md) | Can the habitat support the population over time? | Sensor fusion, time-series analysis, geospatial modeling |
| [Cognitive Aging & Behavioral Change](docs/research-themes/06-cognitive-aging/README.md) | Are behavior patterns changing with age, disease, or stress? | Longitudinal analytics, anomaly detection, multimodal AI |

Reproduction can be studied across these themes through individual life histories, population recruitment, social relationships, and habitat conditions.

## System View

```text
Field devices
  cameras, acoustic nodes, trackers, environmental sensors
        |
        v
Field data layer
  observation records, device metadata, deployment sites
        |
        v
AI capability layer
  vision, bioacoustics, time-series, edge AI, LLM-assisted analysis
        |
        v
Research projects
  species-specific studies, conservation programs, open datasets
```

See [System Architecture](docs/system-architecture.md) for the intended structure.

## Repository Map

| Path | Purpose |
|---|---|
| `docs/` | Vision, architecture, field deployment, data governance, research themes, hardware notes, and AI capability notes |
| `projects/` | Project proposal guidance, reusable project template, and future examples |
| `reference-implementations/` | Lightweight placeholders for future reusable code modules |
| `schemas/` | JSON Schemas for common wildlife research records |
| `.github/` | Issue templates, pull request template, and documentation checks |

## How to Contribute

- Bring a real research question or field deployment problem.
- Propose a project using the project template.
- Improve research theme documentation with domain knowledge.
- Contribute datasets only when permissions, sensitivity, and species risk have been reviewed.
- Add reference implementations once a pattern has been used in a real project.

Start with [CONTRIBUTING.md](CONTRIBUTING.md) and [RESPONSIBLE_RESEARCH.md](RESPONSIBLE_RESEARCH.md).

## Current Status

This repository is in the foundation stage. We are defining shared language, project structure, governance, and minimal data schemas before promoting model code or production pipelines.

## Citation

If this initiative helps your research, please cite the repository using [CITATION.cff](CITATION.cff).

