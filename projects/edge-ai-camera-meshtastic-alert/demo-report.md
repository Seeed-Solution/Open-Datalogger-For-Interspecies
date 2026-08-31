# Demo Validation Notes

This file records the evidence used by the project README. It is intentionally shorter than the main project page.

## Validated Chain

```text
cat detected by reCamera Pro
-> GPIO188 high pulse
-> Wio SX1262 with XIAO ESP32S3 Detection Sensor input
-> Meshtastic alert
-> Wio Tracker L1 Pro receives "Cat detected"
```

## Current Parameters

| Item | Value |
|---|---|
| Proxy target | Stray cat |
| Camera | reCamera Pro 2GB |
| Transmitter | Wio SX1262 with XIAO ESP32S3 |
| Receiver | Wio Tracker L1 Pro |
| Camera GPIO | Linux GPIO188, `CAN0_RXD_M0 / GPIO5_D4` |
| GPIO pulse | 3 seconds high |
| Camera cooldown | 60 seconds |
| Snapshot target size | about 500 KB |
| Snapshot retention | 1000 images, then delete oldest 100 |

## Evidence Files

| File | Purpose |
|---|---|
| `media/mesh-notice.jpg` | Receiver shows the `Cat detected` alert |
| `media/solar-panel-camera.jpg` | Outdoor-style solar deployment test |
| `media/power-supply.jpg` | Power and transmitter setup |
| `media/wiring.jpg` | reCamera Pro to transmitter wiring |
| `media/mesh-channel-configuration.png` | Meshtastic channel settings with key redacted |
| `media/mesh-detection-sensor-configuration.png` | Detection Sensor module settings |
| `media/run-report.jpg` | Runtime dashboard and target-event summary |

## Interpretation

The demo proves that the device chain can work as a deployable workflow. It does not yet prove field-ready model accuracy for any specific wildlife species.

The most important reusable pattern is the boundary between AI and radio: the camera decides whether a target event happened, then a simple GPIO pulse lets a Meshtastic node handle message delivery.

