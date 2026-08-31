# reCamera + Meshtastic Trigger Reference

This reference implementation turns edge AI inference on a reCamera Pro into a simple hardware trigger that can be consumed by a Meshtastic node.

It supports the first demo project:

- [Edge AI Camera to Meshtastic Alert Demo](../../projects/edge-ai-camera-meshtastic-alert/)

## Current Behavior

```text
reCamera Pro inference stream
-> filter for configured target classes
-> output GPIO188 high for 3 seconds
-> keep a 60-second cooldown
-> save a trigger snapshot
-> external Meshtastic node sends the alert
```

## Hardware Roles

| Device | Role |
|---|---|
| reCamera Pro | Runs edge AI detection and controls GPIO |
| Meshtastic transmitter node | Reads the GPIO trigger and sends a radio alert |
| Wio Tracker L1 Pro | Receives the Meshtastic alert |
| Optional ESP32-class bridge | Can be used when custom signal conditioning or message formatting is needed |

## Camera Output

The validated camera-side trigger pin is:

| Signal | Value |
|---|---|
| Linux GPIO | `188` |
| Pin function | `CAN0_RXD_M0 / GPIO5_D4` |
| Logic high | 3.3 V |
| Pulse | 3 seconds |
| Cooldown | 60 seconds |

When this pin is used as GPIO, it should not be used as a CAN bus signal at the same time.

## Files to Add

The implementation files should be promoted here from the validated reCamera Pro handoff package:

```text
scripts/
  person_gpio_trigger.py
  recamera_trigger.conf
  S99recamera_gpio_trigger
  install.sh
  uninstall.sh
  download_snapshots.py

docs/
  wiring.md
  troubleshooting.md
  trigger-snapshots.md
```

This first pass documents the integration point. The code package can be copied in after the public example wording is approved.

## Configuration Shape

```ini
GPIO=188
TARGET_CLASSES=cat
MIN_SCORE=0.10
PULSE_SECONDS=3
COOLDOWN_SECONDS=60
SAVE_SNAPSHOT=1
SNAPSHOT_TARGET_KB=500
SNAPSHOT_MAX_FILES=1000
SNAPSHOT_DELETE_BATCH=100
```

During development, `person` can be included as a test class. For a public wildlife demo, keep the target class and model limitations explicit.

## Integration Boundary

The reCamera Pro should only decide whether a trigger event happened. The Meshtastic node should handle radio-specific behavior:

- message text;
- destination channel;
- retransmission policy;
- receiver display behavior;
- battery-specific sleep strategy.

This boundary keeps the workflow reusable across different field radios and receiver devices.

