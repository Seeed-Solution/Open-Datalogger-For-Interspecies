# Edge AI Camera to Meshtastic Alert Demo

[中文](README.zh-CN.md)

This demo validates a small but important field pattern for Open Datalogger For Interspecies:

```text
edge AI camera detects a target
-> local GPIO signal is triggered
-> Meshtastic node broadcasts an alert
-> field receiver displays the event
```

In the office pilot, a reCamera Pro watches for stray cats around the workplace. When a cat is detected, the camera triggers a GPIO output connected to a Meshtastic transmitter. The alert is then delivered over the Meshtastic network to a Wio Tracker L1 Pro receiver.

The cat is used as a safe, accessible stand-in for a field target. The same chain could later be adapted for wildlife or conservation scenarios such as detecting a tiger, wolf, or potential poacher near a protected area. The goal of this demo is not to claim a production wildlife model; it is to prove that edge detection, physical signaling, and off-grid message delivery can work together as one deployable workflow.

## Why This Matters

Wildlife and conservation teams often need to know that something happened in the field before they can inspect raw photos or video. A camera trap may collect useful images, but the response loop is slow if the device only stores data locally.

This demo explores a faster pattern:

- detect a target locally on the camera;
- save a snapshot as evidence;
- emit a simple GPIO signal;
- let a low-power radio network carry the alert;
- receive the event on a handheld or gateway node.

For future deployments, the detected target could be a species of interest, a livestock conflict risk, a vehicle, or unauthorized human activity.

## Current Demo Scenario

| Item | Demo Setting |
|---|---|
| Site | Office / company area |
| Proxy target | Stray cat |
| Field analogy | Tiger, wolf, or potential poacher |
| Edge device | reCamera Pro |
| Alert network | Meshtastic |
| Receiver | Wio Tracker L1 Pro |
| Trigger signal | GPIO188, 3.3 V high pulse |
| Trigger duration | 3 seconds |
| Cooldown | 60 seconds |
| Evidence | Local trigger snapshot and event log |

## Data Flow

```text
reCamera Pro
  AI inference result: cat/person/etc.
  trigger filter: cat
  snapshot: local JPG
  GPIO188: high pulse
        |
        v
Meshtastic transmitter node
  reads GPIO signal
  sends alert packet
        |
        v
Wio Tracker L1 Pro receiver
  receives field alert
  displays or forwards event
```

## What Was Validated

- The camera can run edge AI inference continuously.
- Detection results can be consumed locally by a script.
- A selected target class can trigger a GPIO pulse.
- A trigger snapshot can be saved for later review.
- GPIO output can be used to notify an external Meshtastic device.
- The Meshtastic network can deliver the alert to a receiver node.

## What This Demo Does Not Prove Yet

- It does not prove a trained tiger or wolf detector is production-ready.
- It does not measure field accuracy, false positives, or missed detections.
- It does not yet define a complete conservation data protocol.
- It does not replace expert review of images, locations, and sensitive species data.

## Reusable Output

The technical workflow is being organized as a reusable reference implementation:

- [reCamera + Meshtastic Trigger Reference](../../reference-implementations/recamera-meshtastic-trigger/)

Future work can swap the demo target class, radio message format, power system, or receiver behavior while keeping the same high-level chain.
